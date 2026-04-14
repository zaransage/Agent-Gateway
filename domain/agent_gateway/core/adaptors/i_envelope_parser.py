import abc
from domain.agent_gateway.core.envelope import Envelope


class IEnvelopeParser(abc.ABC):
    @abc.abstractmethod
    def parse(self, raw: str) -> Envelope:
        """Parse a raw envelope string into an Envelope instance."""
