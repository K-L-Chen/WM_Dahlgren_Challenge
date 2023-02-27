# W&M Dahlgren Innovations Challenge

## Members:
Joseph S. Lee  
Kevin Wu  
Stephen D. Hoag  
Nicholas B. Wilson  
Kyle L. Chen 

## [White Paper](https://docs.google.com/document/d/1Xppf6QdNAMhJ6N96sseM0M005vMf4IOP/edit?usp=sharing&ouid=106865301655792132926&rtpof=true&sd=true)

## [Main Repository](https://github.com/K-L-Chen/WM_Dahlgren_Challenge)

## Prep Notes

**Downloading Files Note**: Whatever files you wish to have on the competition computer (source code, libraries, etc) should be placed within a zip file, with a name making it clear what school/team you represent, and sent to NSWCDD prior to the competition. This zip file will be placed on your competition computer.

**Note About Enemy Missiles**: If physically possible, enemy missiles will redirect to the next "easiest" target if their original target is destroyed. Easiest target is defined as a combination of distance and orientation of possible targets. Targets in line and closer to enemy missiles will be "easier" targets. If enemy missiles cannot acquire or reach a new target they will self-destruct. This means that when a ship dies, existing enemy missiles targeting it could redirect and target another ship if possible.

**Testing scenarios**: When developing your clients, you should strive to complete fully populated scenarios (30 threats, 5 friendly ships, 1 reference ship) in less than 5 minutes in Synchronous (Step) mode. When we test your clients, we will first test in synchronous mode to determine your score if the test scenario completes within the 5-minute time-limit. If it does not complete in time, then your client will be re-run within GUI mode and that score will be used for your team. Note that GUI mode is generally more challenging as it will not wait for a synchronous reply message from your algorithm if it is too slow, and the threats will continue moving in toward your friendly assets regardless of whether your algorithm is sending replies.
