import gui

def run():
    try:
        if hasattr(gui, "main"):
            gui.main()
        else:
            print("Error: main() function not found in gui.py")
    except Exception as e:
        print(f"Critical error in run.py: {e}")

if __name__ == "__main__":
    run()
