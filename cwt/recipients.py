from typing import Any, Dict, List, Optional, Union

import cbor2

from .cose_key_interface import COSEKeyInterface
from .recipient import Recipient
from .recipient_interface import RecipientInterface


class Recipients:
    """
    A Set of COSE Recipients.
    """

    def __init__(self, recipients: List[RecipientInterface]):
        self._recipients = recipients
        return

    @classmethod
    def from_list(cls, recipients: List[Any]):
        """
        Create Recipients from a CBOR-like list.
        """
        res: List[RecipientInterface] = []
        for r in recipients:
            res.append(cls._create_recipient(r))
        return cls(res)

    @classmethod
    def _create_recipient(cls, recipient: List[Any]) -> RecipientInterface:
        if not isinstance(recipient, list) or (
            len(recipient) != 3 and len(recipient) != 4
        ):
            raise ValueError("Invalid recipient format.")
        if not isinstance(recipient[0], bytes):
            raise ValueError("protected header should be bytes.")
        protected = {} if not recipient[0] else cbor2.loads(recipient[0])
        if not isinstance(recipient[1], dict):
            raise ValueError("unprotected header should be dict.")
        if not isinstance(recipient[2], bytes):
            raise ValueError("ciphertext should be bytes.")
        if len(recipient) == 3:
            return Recipient.new(protected, recipient[1], recipient[2])
        if not isinstance(recipient[3], list):
            raise ValueError("recipients should be list.")
        recipients: List[RecipientInterface] = []
        for r in recipient[3]:
            recipients.append(cls._create_recipient(r))
        return Recipient.new(protected, recipient[1], recipient[2], recipients)

    def extract_key(
        self,
        keys: List[COSEKeyInterface],
        context: Optional[Union[Dict[str, Any], List[Any]]] = None,
        alg: int = 0,
    ) -> COSEKeyInterface:
        """
        Extracts an appropriate key from recipients, keys privided as a parameter ``keys``
        or key materials as a parameter ``materials``.
        """
        for r in self._recipients:
            for k in keys:
                if k.kid != r.kid:
                    continue
                return r.decode_key(k, alg=alg, context=context)
        raise ValueError("Failed to derive a key.")
