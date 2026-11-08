"""
Security Manager handling manual login prompts, individual record logging, and privacy controls.
"""
from logger import setup_logger, mask_passport

logger = setup_logger("SecurityManager")

class SecurityManager:
    @staticmethod
    def prompt_manual_login_required() -> bool:
        print("\n" + "="*60)
        print("WAFID SESSION CHECK: NOT AUTHENTICATED / EXPIRED")
        print("="*60)
        print("Your saved browser session is not currently logged into Wafid.")
        print("Would you like to open Microsoft Edge to log in manually?")
        print("="*60)
        while True:
            choice = input("Manual login required. Open Edge now? (YES/NO): ").strip().upper()
            if choice == "YES":
                logger.info("User requested manual login.")
                return True
            elif choice == "NO":
                logger.info("User declined manual login. Returning to main menu.")
                return False
            else:
                print("Please enter exact 'YES' or 'NO'.")

    @staticmethod
    def wait_for_manual_login_completion():
        print("\n" + "-"*60)
        print("Please complete your manual login in the Microsoft Edge window.")
        print("Once you are logged in and on the Wafid main page, press ENTER.")
        print("-"*60)
        input("Press ENTER in CMD after completing login...")
        logger.info("User confirmed manual login completion.")
