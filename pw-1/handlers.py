from typing import Callable
from _classes import AddressBook, Record



def parse_input(user_input:str):
    """Parses the input into a command and list of arguments."""
    if not user_input.strip():
        return "_"
    
    command, *args = user_input.split()
    command = command.strip().lower()
    
    return command, *args

def input_error(func) -> Callable:
    """
    Returns the handler-function or returns an error message.
    """
    def inner(*args, **kwargs):
        try:
            return True, func(*args, **kwargs)
        except ValueError:
            return False, "Enter name and phone please."
        except KeyError:
            return False, "Such contact does not exist."
        except IndexError:
            return False, "Enter user name please."
        except AttributeError:
            return False, "This entry is missing."
        except Exception as e:
            return False, f"{e}"
    return inner

@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    """Adds a contact to the dict (name and phone number)."""
    name, phone_number, *_ = args
    record = book.find(name)
    message = "Contact updated."
    
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone_number:
        record.add_phone(phone_number)
    return message
    
@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    """Updates an existing contact's phone."""
    name, old_phone_number, new_phone_number, *_ = args
    record:Record = book.find(name)
    
    record.edit_phone(old_phone_number, new_phone_number)    
    return "Contact updated."
   
            
@input_error   
def show_phone(args: list[str], book: AddressBook) -> list[str]:
    """Returns a phone number by name."""
    name = args[0].strip().lower()
    record:Record = book.find(name)
    
    phones = [p.value for p in record.phones]
    return phones
      
    
@input_error
def show_all(book: AddressBook) -> AddressBook :
    """Returns all contacts as lines."""
    if not book:
        raise Exception("No contacts yet.")

    return book

@input_error
def add_birthday(args:list[str], book:AddressBook) -> str:
    """Add date of birth for the specified contact in the format DD.MM.YYYY"""
    try:
        name, birthday, *_ = args
    except ValueError:
         raise Exception("Please enter name and date of birth.")
    
    record:Record = book.find(name)
       
        
    if record.birthday:
        message = "Birthday updated."
    else:
        message = 'Birthday added.'
       
    record.add_birthday(birthday)    
    return message

@input_error
def show_birthday(args:list[str], book:AddressBook) -> str:
    """Returns a date of birth by name."""
    try:
        name, *_ = args
    except ValueError:
         raise Exception("Please enter name.")
    
    record:Record = book.find(name)
      
    birthday = record.birthday.value
    if birthday is None:
        raise Exception("The contact does not have a date of birth set.")
    return birthday

@input_error
def birthdays(book:AddressBook) -> list[str]:
    """Returns a list of users to be greeted by day of the week next week"""
    result = book.get_upcoming_birthdays()
    if not result:
        raise Exception("No birthdays in the next 7 days.")
    lines = [f"Name: {item['name']}, birthday: {item['birthday']}" for item in result]
    return lines