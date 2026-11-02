"""Source provenance shared by live and recorded episodes, not truth validation."""
from dataclasses import asdict, dataclass
import math

__version__ = '0.1.0'
KINDS = {'report', 'observation', 'user_correction', 'assistant_statement'}

@dataclass(frozen=True)
class SourceRecord:
    episode_id: str
    source_id: str
    source_time: float
    available_time: float
    kind: str
    version: int = 1

    def __post_init__(self):
        if not self.episode_id or not self.source_id or self.kind not in KINDS or self.version != 1:
            raise ValueError('Invalid source identity, kind or version')
        if any(isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t) or t < 0
               for t in (self.source_time, self.available_time)) or self.available_time < self.source_time:
            raise ValueError('Invalid source times')

    def wire(self):
        return asdict(self)

def available_sources(records, episode_id, cutoff):
    if not math.isfinite(cutoff) or cutoff < 0:
        raise ValueError('Invalid evidence cutoff')
    return {r.source_id: r for r in records if r.episode_id == episode_id and r.available_time <= cutoff}

def check_references(ids, records, episode_id, cutoff):
    allowed = available_sources(records, episode_id, cutoff)
    if any(i not in allowed for i in ids):
        raise ValueError('Unavailable or cross-episode source')
    return tuple(allowed[i] for i in ids)
