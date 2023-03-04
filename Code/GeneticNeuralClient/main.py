"""
To ensure proper functionality, ensure these versions are used for protobuf and pyzmq
pip install protobuf==3.20.0
pip install pyzmq==24.0.0
Developed on python 3.10.9
"""
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_dir", required=True, type=str, help = "Existing relative or global directory to save \
                        each population generation in")
    args = parser.parse_args()

    # Imports
    from pathlib import Path
    if Path(args.save_dir).absolute().exists():
        print("Verified existence of save directory")
        from publisher import Publisher
        from subscriber import Subscriber
        from AiManager import AiManager

        print("Initializing AI client: Genetic-Algorithmic Approach to Neural Nets")

        # Initialize Publisher
        publisher = Publisher()

        # Initialize Subscriber
        subscriber = Subscriber()

        # Initialize AiManager
        ai_manager = AiManager(publisher, args)

        # Register subscriber functions of Ai manager and begin listening for messages
        subscriber.registerSubscribers(ai_manager)
        subscriber.startSubscriber()
    else:
        raise ValueError("Please input a valid save_dir")