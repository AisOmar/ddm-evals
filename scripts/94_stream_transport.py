"""Strict OpenRouter SSE reconstruction; no network, scoring or answer rescue."""
import json


class StreamFailure(ValueError):
    def __init__(self, reason, detail=None):
        self.reason, self.detail = reason, detail
        super().__init__(reason+(':'+str(detail) if detail is not None else ''))


def events(raw):
    try:
        text = raw.decode('utf-8') if isinstance(raw, bytes) else raw
    except UnicodeDecodeError as error:
        raise StreamFailure('invalid_utf8') from error
    if not isinstance(text, str):
        raise StreamFailure('invalid_body_type')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if text and not text.endswith('\n'):
        raise StreamFailure('unterminated_sse_line')
    data, event = [], None
    for line in text.split('\n')[:-1]:
        if line == '':
            if data:
                yield event, '\n'.join(data)
            data, event = [], None
        elif line.startswith(':'):
            continue
        else:
            field, sep, value = line.partition(':')
            if not sep:
                value = ''
            if value.startswith(' '):
                value = value[1:]
            if field == 'data': data.append(value)
            elif field == 'event': event = value
            elif field not in ('id', 'retry'):
                raise StreamFailure('unexpected_sse_field', field)
    if data:
        raise StreamFailure('unterminated_sse_event')


def reconstruct(raw, expected_model, expected_provider, model_aliases=()):
    identity = {}
    content, reasoning, refusals, details = [], [], [], []
    terminal, native_terminal, usage = None, None, None
    done, event_count, accounting_frames = False, 0, 0
    created = None
    for event, payload in events(raw):
        if done:
            raise StreamFailure('event_after_done')
        if payload.strip() == '[DONE]':
            done = True
            continue
        try: frame = json.loads(payload)
        except ValueError as error: raise StreamFailure('malformed_event_json') from error
        if not isinstance(frame, dict): raise StreamFailure('invalid_event_type')
        event_count += 1
        if event == 'error' or frame.get('error'):
            raise StreamFailure('stream_api_error', frame.get('error'))
        for key in ('id', 'model', 'provider'):
            value = frame.get(key)
            if value is not None:
                if not isinstance(value, str) or not value:
                    raise StreamFailure('invalid_identity', key)
                if key in identity and identity[key] != value:
                    raise StreamFailure('identity_changed', key)
                identity[key] = value
        if frame.get('model') not in (None, expected_model, *model_aliases):
            raise StreamFailure('model_mismatch')
        if frame.get('provider') not in (None, expected_provider):
            raise StreamFailure('provider_mismatch')
        if frame.get('created') is not None:
            if type(frame['created']) is not int:
                raise StreamFailure('invalid_created')
            if created is not None and created != frame['created']:
                raise StreamFailure('created_changed')
            created = frame['created']
        frame_usage = frame.get('usage')
        if frame_usage is not None:
            if not isinstance(frame_usage, dict): raise StreamFailure('invalid_usage')
            if usage is not None and usage != frame_usage: raise StreamFailure('usage_changed')
            usage = frame_usage
            accounting_frames += 1
        choices = frame.get('choices')
        if not isinstance(choices, list) or len(choices) > 1:
            raise StreamFailure('invalid_choices')
        if not choices:
            if frame_usage is None: raise StreamFailure('empty_nonaccounting_choices')
            continue
        choice = choices[0]
        if not isinstance(choice, dict) or choice.get('index', 0) != 0 or choice.get('error'):
            raise StreamFailure('invalid_choice')
        delta = choice.get('delta', {})
        if not isinstance(delta, dict) or delta.get('tool_calls') or delta.get('function_call'):
            raise StreamFailure('unexpected_delta')
        if delta.get('role') not in (None, 'assistant'): raise StreamFailure('unexpected_role')
        values = {}
        for key in ('content', 'reasoning', 'refusal'):
            value = delta.get(key)
            if value is not None and not isinstance(value, str): raise StreamFailure('invalid_delta_text', key)
            values[key] = value or ''
        if terminal is not None and (any(values.values()) or delta.get('reasoning_details')):
            raise StreamFailure('content_after_terminal')
        content.append(values['content'])
        reasoning.append(values['reasoning'])
        refusals.append(values['refusal'])
        if delta.get('reasoning_details'):
            if not isinstance(delta['reasoning_details'], list): raise StreamFailure('invalid_reasoning_details')
            details.extend(delta['reasoning_details'])
        finish = choice.get('finish_reason')
        native = choice.get('native_finish_reason')
        if finish is not None:
            if finish not in ('stop', 'length', 'content_filter'):
                raise StreamFailure('invalid_finish_reason', finish)
            if terminal is not None and (finish != terminal or frame_usage is None):
                raise StreamFailure('inconsistent_terminal_frame')
            terminal = finish
        if native is not None:
            if not isinstance(native, str) or (native_terminal is not None and native_terminal != native):
                raise StreamFailure('native_finish_changed')
            native_terminal = native
    if not done: raise StreamFailure('missing_done')
    if terminal is None: raise StreamFailure('missing_terminal')
    if usage is None: raise StreamFailure('missing_usage')
    if set(identity) != {'id', 'model', 'provider'}: raise StreamFailure('missing_identity')
    if identity['model'] not in (expected_model, *model_aliases) or identity['provider'] != expected_provider:
        raise StreamFailure('identity_mismatch')
    for key in ('prompt_tokens', 'completion_tokens'):
        if type(usage.get(key)) is not int or usage[key] < 0: raise StreamFailure('invalid_token_usage', key)
    message = dict(role='assistant', content=''.join(content))
    if any(reasoning): message['reasoning'] = ''.join(reasoning)
    if any(refusals): message['refusal'] = ''.join(refusals)
    if details: message['reasoning_details'] = details
    result = dict(**identity, object='chat.completion', choices=[dict(index=0, message=message,
        finish_reason=terminal, native_finish_reason=native_terminal)], usage=usage)
    if identity['model'] != expected_model:
        result['reported_model'] = identity['model']
        result['model'] = expected_model
    if created is not None: result['created'] = created
    audit = dict(sse_events=event_count, accounting_frames=accounting_frames, done_received=True,
                 terminal_reason=terminal, visible_characters=len(message['content']),
                 reasoning_characters=len(message.get('reasoning', '')), reasoning_used_as_answer=False,
                 reported_model=identity['model'], model_alias_applied=identity['model'] != expected_model)
    return result, audit
