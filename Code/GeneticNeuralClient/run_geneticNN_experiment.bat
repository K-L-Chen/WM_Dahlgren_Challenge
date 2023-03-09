@echo off
call "..\navy_wta_env\Scripts\activate.bat"
python main.py --save_dir pop_gens_round2 --curr_gen_iter 100 >> score_outputs_round2.txt