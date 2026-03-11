from colorama import init, Fore

from abc import ABC, abstractmethod

from _classes import AddressBook

init(autoreset=True)

class View(ABC):
    
    @abstractmethod
    def show_commansd(self, commands_txt: str):
        pass
    
    @abstractmethod
    def show_message(self, text: str, is_error:bool):
        pass
    
    @abstractmethod
    def show_contact_phones(self, phones: list[str]):
        pass
    
    @abstractmethod
    def show_all_contacts(self, records: AddressBook):
        pass
    
    @abstractmethod
    def show_contact_birthday(self, birthday: str):
        pass
    
    @abstractmethod
    def show_congrat_birthdays(self, line_list: list):
        pass
    
    
    
class ConsoleView(View):
    def show_commansd(self, commands_txt: str) -> None:
        print(Fore.YELLOW + commands_txt)
         
    def show_message(self, text: str, is_error: bool = False):
        color = Fore.RED if is_error else Fore.GREEN
        print(color + text)
    
    def show_contact_phones(self, phones: list[str]):
        line = "; ".join(phones)
        print(Fore.BLUE + line)
        
    def show_all_contacts(self, records: AddressBook):
        print(f"{Fore.BLUE}{str(records)}")
        
    def show_contact_birthday(self, birthday: str):
        print(Fore.BLUE + birthday)
        
    def show_congrat_birthdays(self, line_list: list):
        lines = "\n".join(line_list)
        print(Fore.BLUE + lines)