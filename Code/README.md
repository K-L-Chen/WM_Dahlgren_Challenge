This is our directory for raw code.

Make sure to log in with your W&M Gmail:
[Here](https://drive.google.com/drive/folders/14c_LgWjHnV3PtF9zAae1G-9ESDJKL-O-?usp=share_link) is the link to the `3_Planner_Environment` folder to be put into this `Code` directory.

If you are not running a Windows machine, instead of running `Planner_Runner.bat`, create a file called `Planner_Runner.sh` with the following content:

```
#!/usr/bin/sh
Java11=./Java/jdk-11.0.8/bin
"$Java11/java.exe" -cp Planner-3.0-jar-with-dependencies.jar mil.navy.jcore.planner.AppLauncher
sleep infinity
```

Then do `chmod +x Planner_Runner.sh` and then `./Planner_Runner.sh` in your terminal.
