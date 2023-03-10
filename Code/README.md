# AI Client (Our Algorithms) + Simulation Interface

## Download Instructions

On your browser, make sure you are logged in with your William & Mary Google account.

What you see in the [`Planner`](./Planner) directory from GitHub is a modified subset of the files/folders found [here](https://drive.google.com/drive/folders/14c_LgWjHnV3PtF9zAae1G-9ESDJKL-O-?usp=share_link). Download the remaining files/folders and place them here.

## Setup Instructions

1. Locate `Planner/JCORE/JCORE/Data/Base/CommonData/Sensors_Emitters_Base.json` if applicable and change the JSON file title to `Sensors&Emitters_Base.json`

2. Edit the configuration file `metricsApp.config` under the `config` directory as directed.

3a. If on Windows, simply run `Planner_Runner.bat`

3b. If you are not running a Windows machine, instead of running `Planner_Runner.bat`, please run `Planner_Runner.sh` instead.

Then run the following in your terminal:

```
chmod +x ./Java/jdk-11.0.8/bin/java.exe
chmod +x Planner_Runner.sh
./Planner_Runner.sh
```

to see the GUI mentioned in slide 18 of the [planner instruction manual](../Instructions/2_Planner_Instruction_Manual.pdf)

4. You will then configure your Python environment according to the first few lines in [`main.py`](./Planner/PythonClient/main.py):

```
python 3.10.9
pip install protobuf==3.20.0
pip install pyzmq==24.0.0
pip install numpy pandas
```

Then run `python main.py` to get our A.I. up and running.

## [Planner Instruction Manual](../Instructions/2_Planner_Instruction_Manual.pdf)
To thoroughly familiarize yourself with the technical environment, I recommend going through the manual yourself, some of which overlaps with what is said here.
