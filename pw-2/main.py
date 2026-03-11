from colorama import init

from typing import Any, Callable


from handlers import (
    parse_input, 
    add_contact, 
    change_contact,
    show_phone, 
    show_all,
    add_birthday,
    show_birthday,
    birthdays
)
from save_data_func import load_data, save_data
from _viewer import ConsoleView

init(autoreset=True)


bot_comamand_list = """
Commands:
hello - greeting
add [name] [phone number] - adding a username with a phone numbe
change [name] [old phone number] [new phone number]- changing contact phone number by name
phone [name] - search for phone number by contact name
add-birthday [name] [birthday] - add date of birth for the specified contact in the format DD.MM.YYYY
show-birthday [name] - show date of birth for the specified contact
birthdays - show birthdays for the next 7 days with dates when they should be celebrated
all - show all contact list
close, exit - bot shutdown
"""

def handle_result(view: ConsoleView, ok: bool, result: Any, on_success: Callable):
    if not ok:
        view.show_message(result, is_error=True)
        return
    on_success(result)

def with_args(handler: Callable):
    return lambda args, book: handler(args, book)

def without_args(handler: Callable):
    return lambda args, book: handler(book)

command_map = {
    "add": (with_args(add_contact), lambda view, result: view.show_message(result)),
    "change": (with_args(change_contact), lambda view, result: view.show_message(result)),
    "phone": (with_args(show_phone), lambda view, result: view.show_contact_phones(result)),
    "all": (without_args(show_all), lambda view, result: view.show_all_contacts(result)),
    "add-birthday": (with_args(add_birthday), lambda view, result: view.show_message(result)),
    "show-birthday": (with_args(show_birthday), lambda view, result: view.show_contact_birthday(result)),
    "birthdays": (without_args(birthdays), lambda view, result: view.show_congrat_birthdays(result)),
}

def main():
    book = load_data()
    view = ConsoleView()
    
    view.show_message("Welcome to the assistant bot!") 
    view.show_commansd(bot_comamand_list)
        
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)
        
        if command in ["exit", "close"]:
            save_data(book)
            view.show_message("Goodbye!")
            break
        
        elif command == "hello":
            view.show_message("How can I help you?")
            
        elif command in command_map:
            handler, presenter = command_map[command]
            ok, result = handler(args, book)
            handle_result(view, ok, result, lambda result: presenter(view, result))
        else:
            view.show_message("Invalid command.", is_error=True)

if __name__ == "__main__":
    main()
  