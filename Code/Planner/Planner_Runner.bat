SET Java11=.\Java\jdk-11.0.8\bin
"%Java11%\java.exe" -cp Planner-3.0-jar-with-dependencies.jar mil.navy.jcore.planner.AppLauncher
timeout /t -1
cmd /k