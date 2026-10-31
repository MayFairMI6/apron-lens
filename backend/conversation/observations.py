"""What the model reports seeing in the view, related to the received reports.

An observation is a separate, lower-authority kind of evidence: it has its own
capture time and comes from the rendered view rather than a report. It can be
consistent with a report, conflict with one, or appear before any report
exists. It never supersedes, edits or removes a report; a conflict is shown as
unresolved for a person to check.

The links between visible state and report properties below are authored
simulation rules, not operational procedure. For example, a fuel vehicle may
remain at an aircraft for reasons unrelated to fuelling. They require domain
review before any claim beyond this synthetic study.

This module never reads scenario ground truth for visible state.
"""

RULES_NOTE = 'Authored simulation rules, not operational procedure; domain review required.'
# 'appearance' describes how each rendered prop looks, for the prompt's legend. The props are
# abstract shapes, so the model cannot know what they stand for without it.
VISUAL_KINDS = {
    'fuel_vehicle': dict(values=('connected', 'departed'), related_property='fuel_status',
                         suggests={'connected': 'incomplete', 'departed': 'complete'},
                         label='Fuel vehicle',
                         appearance='connected: a near-black tanker (a long rounded tank with a separate cab) beside '
                                    'the forward fuselage, joined to it by a thin hose; departed: no tanker there'),
    'cargo_door': dict(values=('open', 'closed'), related_property='baggage_status',
                       suggests={'open': 'incomplete', 'closed': 'complete'},
                       label='Cargo hatch',
                       appearance='open: a flat near-black flap standing out from the side of the forward fuselage; '
                                  'closed: no flap'),
}
RELATIONS = ('consistent', 'conflicts', 'no_report_yet', 'report_describes_later_time', 'not_comparable')


def relate(observation, snapshot):
    """Relate one observation to the reports in a snapshot of the observed flight.

    The snapshot must be taken at or after the capture time. Report statuses
    in the snapshot are not changed.
    """
    spec = VISUAL_KINDS[observation['kind']]
    prop = spec['related_property']
    capture = observation['captureTime']
    if capture > snapshot['cutoff']:
        raise ValueError('Observation captured after the snapshot cutoff')
    active = [f for f in snapshot['facts'] if f['property'] == prop and f['status'] in ('current', 'conflicting')]
    if not active:
        relation, cited = 'no_report_yet', []
    else:
        earlier = [f for f in active if f['eventTime'] <= capture]
        if not earlier:
            relation, cited = 'report_describes_later_time', [f['event_id'] for f in active]
        else:
            cited = [f['event_id'] for f in earlier]
            reported_complete = {f['value'] for f in earlier} == {'complete'}
            suggestion = spec['suggests'][observation['value']]
            if reported_complete and suggestion == 'complete':
                relation = 'consistent'
            elif reported_complete and suggestion == 'incomplete':
                relation = 'conflicts'
            else:
                relation = 'not_comparable'
    return dict(kind=observation['kind'], value=observation['value'], captureTime=capture,
                relatedProperty=prop, relation=relation, evidenceIds=cited, rulesNote=RULES_NOTE)


def describe(related):
    label = VISUAL_KINDS[related['kind']]['label']
    head = f"Visual observation at {related['captureTime']:g} s (not verified): {label.lower()} {related['value']}"
    ids = ', '.join(related['evidenceIds'])
    tail = {
        'consistent': f'consistent with report {ids}.',
        'conflicts': f'conflicts with report {ids}; unresolved, and the report is unchanged.',
        'no_report_yet': f"no {related['relatedProperty']} report received yet; this does not establish the service state.",
        'report_describes_later_time': f'report {ids} describes a later time than this view.',
        'not_comparable': f'not directly comparable with report {ids}.',
    }[related['relation']]
    return head + ' — ' + tail
