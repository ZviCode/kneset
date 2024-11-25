from dataclasses import dataclass

@dataclass
class KnessetMember:
    mk_id: int
    firstname: str
    lastname: str
    faction_name: str
    is_coalition: bool
    is_present: bool
    image_path: str

    @classmethod
    def from_api_response(cls, data):
        return cls(
            mk_id=data['MkId'],
            firstname=data['Firstname'],
            lastname=data['Lastname'],
            faction_name=data['FactionName'],
            is_coalition=data['IsCoalition'],
            is_present=data['IsPresent'],
            image_path=data['ImagePath']
        )