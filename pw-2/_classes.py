from collections import UserDict
from datetime import datetime, timedelta


class FormatPhoneNumber(Exception):
    pass

class Field:
    """Base class for record fields."""
    
    def __init__(self, value:str):
        self.value = value
    
    def __str__(self):
        return str(self.value)

class Name(Field):
    """Class for storing a contact name. Required field."""
    pass

class Phone(Field):
    """Class for storing a phone number. Validates format (10 digits)."""
    def __init__(self, value:str):
        super().__init__(value)
        if len(value) !=10:
            raise FormatPhoneNumber("Phone number must consist of 10 digits")
        if not value.isdigit():
                raise FormatPhoneNumber("The phone number must contain only numbers.")
                
    

class Birthday(Field):
    def __init__(self, birthday_date:str):
        try:
            datetime.strptime(birthday_date, '%d.%m.%Y') 
        except ValueError:
            raise Exception("Invalid date format. Use DD.MM.YYYY")
        else:
            super().__init__(birthday_date)

class Record:
    """
    Class for storing contact info, including a name and a list of phone numbers.
    Add phone numbers.
    Remove phone numbers.
    Edit phone numbers.
    Search for a phone number.
    Add birthday.
    Show the contact's birthday.
    Show a list of users to be greeted by day of the week next week.
    """
    def __init__(self, name:str):
        self.name = Name(name)
        self.phones: list[str] = []
        self.birthday = None
        
    def add_phone(self, phone_number:str):
        self.phones.append(Phone(phone_number))
        
    def remove_phone(self, phone_number:str):
        phone = self.find_phone(phone_number)
        if not phone:
            raise ValueError("Phone number not found.")
        self.phones.remove(phone)
        
    def edit_phone(self, old_phone_number:str, new_phone_number:str):
        phone = self.find_phone(old_phone_number)
        if not phone:
            raise Exception("Phone number not found.")
        self.phones[self.phones.index(phone)] = Phone(new_phone_number)
        
    def find_phone(self, phone_number:str):
        return next((phone for phone in self.phones if phone.value == phone_number), None)
    
    def add_birthday(self, birhday_date:str):
        self.birthday = Birthday(birhday_date)
    
    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday_value = self.birthday.value if self.birthday else "no date"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday_value}"

class AddressBook(UserDict):
    """
    Class for storing and managing records.
    Add records.
    Find records by name.
    Delete records by name.
    Record: add phone numbers.
    """
    def add_record(self, new_record):
        self.data[new_record.name.value] = new_record
        
    def find(self, contact_name:str):
        return self.data.get(contact_name)
            
    def delete(self, contact_name:str):
        contact = self.data.get(contact_name)
        if contact:
            self.data.pop(contact_name)
    
    def get_upcoming_birthdays(self):
        today = datetime.now().date()
        end_date = today + timedelta(days=7)
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday_date = datetime.strptime(
                record.birthday.value, "%d.%m.%Y"
            ).date()
            birthday_this_year = birthday_date.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            days_until_birthday = (birthday_this_year - today).days
            if 0 <= days_until_birthday <= 7:
                greeting_date = birthday_this_year
                if greeting_date.weekday() >= 5:
                    greeting_date += timedelta(days=7 - greeting_date.weekday())

                if greeting_date > end_date:
                    continue

                upcoming_birthdays.append(
                    {
                        "name": record.name.value,
                        "birthday": greeting_date.strftime("%d.%m.%Y"),
                    }
                )

        return upcoming_birthdays
            
    def __str__(self):
        lines = []
        for record in self.data.values():
            lines.append(str(record))
        return "\n".join(lines)
