import random
from colorama import Fore, Style

logo_list = [
    '''
     ▄▀▀█▄▄▄▄  ▄▀▀▄▀▀▀▄  ▄▀▀█▄   ▄▀▀▀▀▄   ▄▀▀▀▀▄   ▄▀▀▄▀▀▀▄ 
    ▐  ▄▀   ▐ █   █   █ ▐ ▄▀ ▀▄ █     ▄▀ █      █ █   █   █ 
      █▄▄▄▄▄  ▐  █▀▀█▀    █▄▄▄█ ▐ ▄▄▀▀   █      █ ▐  █▀▀█▀  
      █    ▌   ▄▀    █   ▄▀   █   █      ▀▄    ▄▀  ▄▀    █  
     ▄▀▄▄▄▄   █     █   █   ▄▀     ▀▄▄▄▄▀  ▀▀▀▀   █     █   
     █    ▐   ▐     ▐   ▐   ▐          ▐          ▐     ▐   
     ▐   
    ''',
    '''
    ███████╗██████╗  █████╗ ███████╗ ██████╗ ██████╗ 
    ██╔════╝██╔══██╗██╔══██╗╚══███╔╝██╔═══██╗██╔══██╗
    █████╗  ██████╔╝███████║  ███╔╝ ██║   ██║██████╔╝
    ██╔══╝  ██╔══██╗██╔══██║ ███╔╝  ██║   ██║██╔══██╗
    ███████╗██║  ██║██║  ██║███████╗╚██████╔╝██║  ██║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
                                                 
    ''',
    '''
    ▓█████  ██▀███   ▄▄▄      ▒███████▒ ▒█████   ██▀███
    ▓█   ▀ ▓██ ▒ ██▒▒████▄    ▒ ▒ ▒ ▄▀░▒██▒  ██▒▓██ ▒ ██▒
    ▒███   ▓██ ░▄█ ▒▒██  ▀█▄  ░ ▒ ▄▀▒░ ▒██░  ██▒▓██ ░▄█ ▒
    ▒▓█  ▄ ▒██▀▀█▄  ░██▄▄▄▄██   ▄▀▒   ░▒██   ██░▒██▀▀█▄
    ░▒████▒░██▓ ▒██▒ ▓█   ▓██▒▒███████▒░ ████▓▒░░██▓ ▒██▒
    ░░ ▒░ ░░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░▒▒ ▓░▒░▒░ ▒░▒░▒░ ░ ▒▓ ░▒▓░
     ░ ░  ░  ░▒ ░ ▒░  ▒   ▒▒ ░░░▒ ▒ ░ ▒  ░ ▒ ▒░   ░▒ ░ ▒░
       ░     ░░   ░   ░   ▒   ░ ░ ░ ░ ░░ ░ ░ ▒    ░░   ░
       ░  ░   ░           ░  ░  ░ ░        ░ ░     ░
                              ░
    ''',
    # '''
    #                                ▄▄████▄
    #                           ▄▄@████▓█▌
    #                      ,▄@██▀▀└  -"▀██▓█▄▄
    #                  ▄▄@▓▓▀▀           -▀▀█████▄▄
    #              ▄▄▓▓▓▀▀-                   -▀▀████▄▄
    #         ╓▄▄▓▒▓▓▀-                            ▀▀████▄▄
    #     ▄▄▓▒╣╢▓▀▀                                     ▀▌▀▓▓█▄
    #   ██▓▀▓╣▒▀                                           ▐▒█▓█▓▌
    #   █╣▓▓▒█═                                 ,█▌      ,   ▓▒▐▓█▓█
    #    ╘▀▀-                                   ▀▀▌███▄▄▄mÑ▀▒▄█▓▓█▀
    #                                               -¬-▀▀▀▀▀▀└-
    # '''
]


def log_erazor_tag():
    max = len(logo_list)
    num = random.randint(0, max-1)
    tag = logo_list[num]

    if num == 1:
        tag = tag.replace('█', f'{Fore.MAGENTA}█{Style.RESET_ALL}')
    elif num == 3:
        tag = tag.replace('█', f'{Fore.MAGENTA}█{Style.RESET_ALL}')
    # tag = tag.replace('╚', f'{Fore.BLUE}█{Style.RESET_ALL}')
    # tag = tag.replace('╗', f'{Fore.BLUE}█{Style.RESET_ALL}')
    # tag = tag.replace('╝', f'{Fore.BLUE}█{Style.RESET_ALL}')
    # tag = tag.replace('╔', f'{Fore.BLUE}█{Style.RESET_ALL}')
    # tag = tag.replace('═', f'{Fore.BLUE}█{Style.RESET_ALL}')
    # tag = tag.replace('║', f'{Fore.BLUE}█{Style.RESET_ALL}')
    print(tag)

if __name__ == '__main__':
    log_erazor_tag()