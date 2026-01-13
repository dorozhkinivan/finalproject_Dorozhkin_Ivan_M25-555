from valutatrade_hub.cli.interface import CLI


def main():
    try:
        app = CLI()
        app.run()
    except KeyboardInterrupt:
        print("\nПринудительное завершение.")

if __name__ == "__main__":
    main()