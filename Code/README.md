# AI Client (Our Algorithms) + Simulation Interface

On your browser, make sure you are logged in with your William & Mary Google account.

What you see in the [`Planner`](./Planner) directory from GitHub is a modified subset of the files/folders found [here](https://drive.google.com/drive/folders/14c_LgWjHnV3PtF9zAae1G-9ESDJKL-O-?usp=share_link). Download the remaining files/folders and place them here.

Locate `Planner/JCORE/JCORE/Data/Base/CommonData/Sensors_Emitters_Base.json` if applicable and change the JSON file title to `Sensors&Emitters_Base.json`

If you are not running a Windows machine, instead of running `Planner_Runner.bat`, please run `Planner_Runner.sh` instead.

Then run the following in your terminal:

```
chmod +x ./Java/jdk-11.0.8/bin/java.exe
chmod +x Planner_Runner.sh
./Planner_Runner.sh
```

to see the GUI mentioned in slide 18 of the [planner instruction manual](../Instructions/2_Planner_Instruction_Manual.pdf)

You will then configure your Python environment according to the first few lines in [`main.py`](./Code/Planner/PythonClient/main.py):

```
python 3.10.9
pip install protobuf==3.20.0
pip install pyzmq==24.0.0
```
