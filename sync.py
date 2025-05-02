"""Sync management"""

from secrets_vault.models import ContactType, Organization, Contact, User
from secrets_vault import constants
from secrets_vault.controllers.audit import create_log, create_log_field
from secrets_vault.models import AuditLogFieldType
from secrets_vault.serializers import ContactSyncSerializer

class SyncManagement():
    """
     SyncManagement class is to manage sync related tasks.

    """

    def create_contact(self, data, system_user_id, user_ip_address):
        """
            Method for creating contact.

            Parameters:
                data : consisting of contact data.
                system_user_id (int): The id of the system that creates contact.
                user_ip_address (str): The IP address of the user making the request.

            Returns:
                Contact Response
        """
        # mandatory fields i.e; contacttype, organization and
        # there respective default values were added to the request body before creation.
        contact_type_object = ContactType.objects.get(name = 'IT Staff')
        organization_object = Organization.objects.get(name = "own, Inc.")
        system_user = User.objects.get(id = system_user_id)
        data['is_vip'] = 'No'
        data['contact_type'] = contact_type_object
        data['organization'] = organization_object
        data["created_by"] = system_user
        data["updated_by"] = system_user

        obj = Contact.objects.create(**data)

        action_type = constants.CONTACT_CREATE
        contact_domain = constants.CONTACT_DOMAIN
        client_id = obj.organization.msp_engagement.client.id
        client_name = obj.organization.msp_engagement.client.name
        engagement_id = obj.organization.msp_engagement.id
        engagement_name = obj.organization.msp_engagement.name
        organization_id = obj.organization.id
        organization_name = obj.organization.name

        audit_log = create_log(contact_domain, action_type, client_id, client_name, engagement_id, 
                engagement_name, organization_id, organization_name, obj.id,
                # contact first name and last name both need to recorded in audit. 
                obj.first_name + " " + obj.last_name, system_user_id, user_ip_address)

        field_type_objs = AuditLogFieldType.objects.filter(domain=contact_domain).all()

        if not field_type_objs:
            raise AuditLogFieldType.DoesNotExist("No associated field types found for the domain: {}".format(contact_domain))

        for field_type_obj in field_type_objs:
            if field_type_obj.name in data:
                if hasattr(data[field_type_obj.name], 'name'):
                    data[field_type_obj.name] =  data[field_type_obj.name].name
                create_log_field(audit_log, field_type_obj, None, data[field_type_obj.name], 
                                system_user_id)
                
        return obj
    

    def update_contact(self, contact_object, data, system_user_id, user_ip_address):
        """
            Method to update contact associated with user.
            and to record audit and auditlog fields.

            Parameters:
                user_obj (User) : instance of the user model.
                contact_json : consisting of contact data.
                system_user_id (int): The id of the system that creates contact.
                user_ip_address (str): The IP address of the user making the request.

            Returns:
                Contact Response
        """

        before_value = ContactSyncSerializer(contact_object)
        for key, value in data.items():
            setattr(contact_object, key, value)
        contact_object.save()
        contact_obj_json = ContactSyncSerializer(contact_object)
 
        contact_obj_json = contact_obj_json.data
        
        action_type = constants.CONTACT_UPDATE
        contact_domain = constants.CONTACT_DOMAIN
        client_id = contact_object.organization.msp_engagement.client.id
        client_name = contact_object.organization.msp_engagement.client.name
        engagement_id = contact_object.organization.msp_engagement.id
        engagement_name = contact_object.organization.msp_engagement.name
        organization_id = contact_object.organization.id
        organization_name = contact_object.organization.name

        audit_log = create_log(contact_domain, action_type, client_id, client_name, engagement_id, 
                engagement_name, organization_id, organization_name, contact_object.id, 
                # contact first name and last name both need to recorded in audit.
                contact_object.first_name + " " + contact_object.last_name, 
                system_user_id, user_ip_address)

        field_type_objs = AuditLogFieldType.objects.filter(domain=contact_domain).all()

        if not field_type_objs:
            raise AuditLogFieldType.DoesNotExist("No associated field types found for the domain: {}".format(contact_domain))
        for field_type_obj in field_type_objs:
            if field_type_obj.name in contact_obj_json:
                if before_value[field_type_obj.name] != contact_obj_json[field_type_obj.name]:
                    create_log_field(audit_log, field_type_obj, before_value[field_type_obj.name], contact_obj_json[field_type_obj.name], system_user_id)

    
