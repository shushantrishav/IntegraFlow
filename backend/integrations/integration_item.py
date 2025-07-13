# backend/integrations/integration_item.py
from datetime import datetime
from typing import Optional, List


class IntegrationItem:
    def __init__(
        self,
        id: Optional[str] = None,
        type: Optional[str] = None,
        directory: bool = False,
        parent_path_or_name: Optional[str] = None,
        parent_id: Optional[str] = None,
        name: Optional[str] = None,
        creation_time: Optional[datetime] = None,
        last_modified_time: Optional[datetime] = None,
        url: Optional[str] = None,
        children: Optional[List[str]] = None,
        mime_type: Optional[str] = None,
        delta: Optional[str] = None,
        drive_id: Optional[str] = None,
        visibility: Optional[bool] = True,
        # HubSpot & Notion shared metadata
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        company_name: Optional[str] = None,
        employment_role: Optional[str] = None,
        lead_status: Optional[str] = None,
        # Notion-specific or CRM shared fields
        location: Optional[str] = None,
        domain: Optional[str] = None,
    ):
        self.id = id
        self.type = type
        self.directory = directory
        self.parent_path_or_name = parent_path_or_name
        self.parent_id = parent_id
        self.name = name
        self.creation_time = creation_time
        self.last_modified_time = last_modified_time
        self.url = url
        self.children = children
        self.mime_type = mime_type
        self.delta = delta
        self.drive_id = drive_id
        self.visibility = visibility

        # CRM shared fields
        self.email = email
        self.phone_number = phone_number
        self.company_name = company_name
        self.employment_role = employment_role
        self.lead_status = lead_status
        self.location = location
        self.domain = domain

    def to_clean_dict(self):
        result = self.__dict__.copy()

        # Drop None values
        result = {k: v for k, v in result.items() if v is not None}

        # Drop directory if False
        if result.get("directory") is False:
            result.pop("directory")

        # Drop visibility if True
        if result.get("visibility") is True:
            result.pop("visibility")

        return result
