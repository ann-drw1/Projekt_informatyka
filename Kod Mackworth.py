# import do pracy na plikach
import os

# import do pracy z plikami csv, sluży do zapisu wyników testu
import csv

# import do pracy z plikami yaml, sluży do odczytu konfiguracji
import yaml

# import do losowania licz losowych
import random

# import do funkcji wykonywanych po zakończeniu programu (zapisanie wyników)
import atexit

# import do pracy z plikami o różnych kodowaniach
import codecs

# import do funkcji matematycznych (wykorzystane przy tworzeniu zegara)
import math

# import do typów listy i słownika
from typing import List, Dict

# import do tworzenia ścieżek plików
from os.path import join

# import do elementów wizualnych (visual), obsługi zdarzeń I/0 (event), logów (logging), prostych interfejsów graficznych (gui), funkcji domyślnych (core)
from psychopy import visual, event, logging, gui, core

# Stwórz folder 'results', jeśli go nie ma
os.makedirs('results', exist_ok=True)

# Zmienne Globalne
RESULTS = [['PART_ID', 'Background', 'Time', 'Reaction Time', 'RT diff', 'Type']]
PART_ID = ''
BACKGROUND = ''


# Zapis wyników po zamknięciu programu
@atexit.register
def save_beh_results():
    file_name = f'{PART_ID}_{random.randint(100, 999)}_beh.csv'  # Generacja nazwy pliku z wynikami
    with open(join('results', file_name), 'w',
              encoding='utf-8') as beh_file:  # Stworzenie pliku z wynikami w folderze 'results' i jego otworzenie
        writer = csv.writer(beh_file)
        writer.writerows(RESULTS)  # Zapis wyników do pliku
    logging.flush()  # Wymuszenie zapisania logów


# Wczytanie konfiguracji
conf = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.SafeLoader)

# Gui i dane uczestniak
info = {'ID': '', 'Płeć': ['M', 'F'], 'Wiek': '', 'Tło': ['bialy', 'czarny']}  # Tworzenie słownika z infprmacjami
dict_dlg = gui.DlgFromDict(dictionary=info,
                           title='Eksperyment czujnosci uwagowej')  # Tworzenie okna do wprowadzenia infromacji
if not dict_dlg.OK:  # Obsługa zamknięcia okna do wprowadzenia infromacji
    core.quit()
PART_ID = f"{info['ID']}{info['Płeć']}{info['Wiek']}"  # Przekształcenie wprowadzonych infromacji
BACKGROUND = info['Tło']

# Ustawienia kolorów na podstawie wcześniej odczytanej wartości
if BACKGROUND == 'bialy':
    bg_color = [1, 1, 1]  # białe tło
    clock_color = [-1, -1, -1]  # czarny zegar
else:
    bg_color = [-1, -1, -1]  # czarne tło
    clock_color = [1, 1, 1]  # biały zegar

win = visual.Window(conf['SCREEN_RES'], fullscr=True, units='pix', color=bg_color)  # Tworzenie głównego okna
event.Mouse(visible=False, newPos=None, win=win)  # Obsługa myszy (ukrycie kursora i powiązanie go z głównym oknem)
clock = core.Clock()  # Tworzy zegar do pomiaru czasu
test_clock = core.Clock()  # Tworzy główny zegar do testu

positions = []  # Przygotowanie pustej listy na pozycje kropek
radius = 300  # Przypisanie promienia zegaru
for i in range(12):
    angle = i * 30  # Wyliczanie pozycji kropki w układzie biegunowym
    x = radius * math.sin(math.radians(angle))  # Przeliczanie pozycji z układu biegunowego na karteziański
    y = radius * math.cos(math.radians(angle))
    positions.append((x, y))  # Dodanie wyliczonej pozycji do listy

# parametry kropek (wypełnione okręgi o zadanym promieniu)
dots = [visual.Circle(win, radius=10, pos=pos, fillColor=clock_color, lineColor=clock_color) for pos in positions]


# definicja funkcji rysującej zegar, parametr decyduje o pozycji wskazówki
def draw_clock(position):
    for dot in dots:
        dot.draw()  # Rysowanie kropek zgodnie z ustalonymi wcześniej parametrami
    needle = visual.Line(  # Definiowanie parametrów wskazówki zegara
        win,  # Wybranie okna głównego jako miejsca do narysowania wskazówki
        start=(0, 0),  # Początek lini jaką jest wskazówka zawsze jest na środku ekranu, czyli na środku zegara
        end=positions[position % 12],
        # koniec wskazówki jako jedna z wcześniej wyliczonych pozycji kropek, decyduje o pozycji wskazówki
        lineColor=conf['NEEDLE_COLOR'],  # parametry wizualne wskazówki
        lineWidth=8  # szerokość wskazówki
    )
    needle.draw()  # Rysowanie wskazówki zgodnie z ustalonymi wcześniej parametrami


# definicja funkcji wypisującej tekst, parametr decyduje o jego treści
def show_text(message):
    msg = visual.TextStim(win, text=message, height=24, wrapWidth=1000,
                          color=clock_color)  # Tworzenie obiektu tekstowego (Psychopy)
    msg.draw()  # Narysowanie tekstu
    win.flip()  # Aktualizacja okna głównego
    keys = event.waitKeys(
        keyList=['space', 'escape'])  # Program po wysietleniu tekstu czeka na jeden z dwóch klawiszy (space, esc)
    if 'escape' in keys:  # Jeśli naciśniety zostanie esc to okno się zamyka i program kończy działanie
        win.close()
        core.quit()
    win.flip()  # Jeśli naciśnięty zostanie space to okno głowne się aktualizuje ponownie co usuwa tekst


# definicja funkcji do rozpoczęcia testu, parametr 1 decyduje o długości trwania, parametr 2 decyduje o tym czy to test właściwy czy treningowy
def run_session(duration_sec, is_training=False):
    pos = 0
    tick_timer = core.Clock()  # odlicza czas 1s
    test_clock.reset()
    trial_clock = core.Clock()
    pending_stimulus = None  # Określa czy w danej sekundzie występuje bodziec
    last_space_time = -99
    tick_count = 0  # informuje w, której sekundzie działania testu jest program

    # wybór sekund, w których wystąpi bodziec
    num_stimuli = min(duration_sec, int(duration_sec * conf[
        'STIM_PROB']))  # liczba bodzcow w sesji obliczona na podstawie 'STIM_PROB'
    stimuli_seconds = sorted(
        random.sample(range(duration_sec), num_stimuli))  # Losowo wybrane sekundy w których wystąpią bodzce
    stimuli_set = set(stimuli_seconds)  # Przekształcenie bodzcow na set z uwagi na optymalizację programu

    # narysowanie zegaru na pozycji startowej i odczekanie 1s
    draw_clock(pos)
    win.flip()
    core.wait(1)

    while test_clock.getTime() < duration_sec:

        # Kod wykonuje się co 1s
        if tick_timer.getTime() >= 1.0:
            tick_timer.reset()

            # ustalane jest czy w obecnej sekundzie powinien wystąpić bodziec
            is_stimulus = tick_count in stimuli_set

            # ustalna jest nowa pozycja wskazówki. Jej wartosc jest rowna aktualnej pozycji + przesunięcie, przesunięcie wynosi 1 jeśli w danej sekundzie nie wystąpuje bodziec lub 2 jeśli występuje
            move = 2 if is_stimulus else 1
            pos = (pos + move) % 12

            # zmiana pozycji wskazówki na podstawie nowe pozycji
            draw_clock(pos)
            win.flip()

            # zapisanie czasu wystąpienia bodżca
            stim_time = test_clock.getTime()

            # Jeśli bodziec występuje to jest tworzony wstępny wpis w wynikach oraz zostaje zapisany indeks rekordu do póżniejszej modyfikacji wpisu w wynikach oraz czas bodzca
            if is_stimulus and not is_training:
                index = len(RESULTS)
                RESULTS.append([
                    PART_ID, BACKGROUND,
                    round(stim_time, 3),  # czas bodźca
                    'NA',  # czas odpowiedzi
                    'NA',  # czas reakcji
                    'brak reakcji'  # typ
                ])
                pending_stimulus = (stim_time, index)
            else:
                pending_stimulus = None

            # zwiększenie wartości licznika o 1
            tick_count += 1

        # obsługa naciśnięć klawiszy
        keys = event.getKeys(timeStamped=test_clock)
        for key, key_time in keys:

            # po naciśnięciu esc program wyświetlni stosowny tekst i się zakończy
            if key == 'escape':
                show_text("Eksperyment został przerwany.")
                win.close()
                core.quit()

            # obsługa działania przy naciśnięciu spacji
            if key == 'space':

                # jeśli spacja była naciśnięta zbyt niedawno temu to program je pominie
                if key_time - last_space_time < 0.3:
                    continue

                # ustalenie nowego czasu ostatniego naciśnięcia spacji
                last_space_time = key_time

                # jeśli obecnie występuje bodziec to:
                if pending_stimulus and not is_training:
                    stim_time, index = pending_stimulus
                    rt = round(key_time - stim_time, 3)  # wyliczenie czasu reakcji
                    RESULTS[index][3] = round(key_time, 3)  # przypisanie czasu nacisniecia przycisku
                    RESULTS[index][4] = rt  # przypisanie czas rekacji
                    RESULTS[index][5] = 'bodziec'  # przypisanie typu reakcji
                    pending_stimulus = None

                # jeśli nie występuje bodziec to zostaje dodany nowy wpis do wyników z odpowiednim typem
                elif not is_training:
                    RESULTS.append([
                        PART_ID, BACKGROUND,
                        round(key_time, 3), 'NA', 'NA', 'blad'
                    ])

        # krótkie oczekiwanie optymalizujące działanie sesji
        core.wait(0.01)


# Wyświetlenie instrukcji początkowej
show_text("INSTRUKCJA\n\n"
          "W tym zadaniu Twoim celem jest zachowanie koncentracji przez dłuższy czas.\n"
          "Na ekranie pojawi się zegar z czerwoną wskazówką.\n"
          "Wskazówka będzie poruszać się co sekundę, przeskakując o jedno pole. \n\n"
          "Twoje zadanie: \n\n"
          "Naciśnij spację, gdy tylko zauważysz, że wskazówka przeskoczyła o dwa pola, zamiast jednego.\n\n"
          "Przeskoki o jedno pole = NIC NIE NACISKAJ\n"
          "Przeskok o dwa pola = NACISKAJ SPACJĘ \n\n"
          "Przed właściwym testem wykonasz krótką próbę.\n"
          "Zachowaj ciszę i skupienie.\n"
          "Zadanie potrwa 30 minut.\n"
          "Gdy jesteś gotowy/a, naciśnij spację.\n")

# wyswołanie sekwencji testowej, bez zapisywania danych do wyników
test_clock.reset()
run_session(conf['TRAINING_DURATION'], is_training=True)

# wyswietlenie tekstu
show_text(
    "Trening zakończony.\n\nZaraz rozpocznie się główny test trwający 30 minut.\n\nNaciśnij SPACJĘ, aby kontynuować.")

# rozpoczęcie sesji właściwej z zapisywaniem wyników
test_clock.reset()
run_session(conf['SESSION_DURATION'] * 60)

# wyświetlenie tekstu końcowego i zakończenie działania programu
show_text("Dziękujemy za udział!\n\nMożesz zamknąć okno.")
win.close()