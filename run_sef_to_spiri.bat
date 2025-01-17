@echo off
REM Prelazak u direktorijum gde se nalazi sef_to_spiri.py
cd /d "C:\dev\scripts\sef_to_spiri"

REM Pokretanje Python skripta bez otvaranja konzole
start "" pythonw sef_to_spiri_processor.py %*

