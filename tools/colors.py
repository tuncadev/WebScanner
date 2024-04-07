from colorama import Fore, Style


class ChangeColor:

    def make_white(self, prompt):
        text = f"{Fore.LIGHTWHITE_EX + prompt + Style.RESET_ALL}"
        return text

    def make_red(self, prompt):
        text = f"{Fore.LIGHTRED_EX + prompt + Style.RESET_ALL}"
        return text

    def make_yellow(self, prompt):
        text = f"{Fore.LIGHTYELLOW_EX + prompt + Style.RESET_ALL}"
        return text

    def make_green(self, prompt):
        text = f"{Fore.LIGHTGREEN_EX + prompt + Style.RESET_ALL}"
        return text
