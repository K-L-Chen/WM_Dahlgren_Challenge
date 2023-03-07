"""
To ensure proper functionality, ensure these versions are used for protobuf and pyzmq
pip install protobuf==3.20.0
pip install pyzmq==24.0.0
Developed on python 3.10.9
"""
import argparse
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_dir", required=True, type=str, help = "Existing relative or global directory where \
                        a population generation is stored in")

    parser.add_argument("--curr_gen_iter", required=False, type=int, help="The current generation iteration number to start off on, starting from 0 \n\
                        This implies that you have an existing .pt file you want to start off from in save_dir")
    args = parser.parse_args()

    path_to_save_dir = Path(args.save_dir).absolute()

    if path_to_save_dir.exists():
        print("Verified existence of save directory")

        if not args.curr_gen_iter or (path_to_save_dir / f'pop_gen{args.curr_gen_iter - 1}.pt').exists():
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
            raise ValueError("The curr_gen argument is invalid since you do not have a corresponding .pt population to start off from.")
    else:
        raise ValueError("Please input a valid save_dir")