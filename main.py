import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import os
import json
import subprocess
import threading
import time
from datetime import datetime, timedelta

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GameCard(ctk.CTkFrame):
    def __init__(self, parent, game_data, delete_callback, play_callback, update_cover_callback):
        super().__init__(parent, fg_color=("#E0E0E0", "#2b2b2b"))

        self.game_data = game_data
        self.delete_callback = delete_callback
        self.play_callback = play_callback
        self.update_cover_callback = update_cover_callback

        self.grid_columnconfigure(1, weight=1)

        self.cover_label = ctk.CTkLabel(self, text="", width=100, height=140)
        self.cover_label.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="w")
        self.load_cover()

        self.cover_label.bind("<Double-Button-1>", self.change_cover)

        game_name = os.path.basename(game_data['name'])
        self.name_label = ctk.CTkLabel(
            self,
            text=game_name,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w"
        )
        self.name_label.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="w")

        playtime_hours = game_data.get('playtime', 0) / 3600
        self.playtime_label = ctk.CTkLabel(
            self,
            text=f"Время игры: {playtime_hours:.1f} ч.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70"),
            anchor="w"
        )
        self.playtime_label.grid(row=1, column=1, padx=10, pady=0, sticky="w")

        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=2, column=1, padx=10, pady=(5, 10), sticky="w")

        self.play_button = ctk.CTkButton(
            buttons_frame,
            text="▶️ Играть",
            command=self.play_game,
            width=100,
            fg_color=("#1f6aa5", "#1f6aa5"),
            hover_color=("#144870", "#144870")
        )
        self.play_button.pack(side="left", padx=(0, 10))

        self.delete_button = ctk.CTkButton(
            buttons_frame,
            text="🗑️ Удалить",
            command=self.delete_game,
            width=100,
            fg_color=("#d32f2f", "#c62828"),
            hover_color=("#b71c1c", "#b71c1c")
        )
        self.delete_button.pack(side="left")
    
    def load_cover(self):
        cover_path = self.game_data.get('cover', '')

        if cover_path and os.path.exists(cover_path):
            try:
                image = Image.open(cover_path)
                image = image.resize((100, 140), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=image, dark_image=image, size=(100, 140))
                self.cover_label.configure(image=photo, text="")
                self.cover_label.image = photo
            except Exception as e:
                print(f"Ошибка загрузки обложки: {e}")
                self.set_default_cover()
        else:
            self.set_default_cover()
    
    def set_default_cover(self):
        self.cover_label.configure(
            text="🕹️\n\nДвойной\nклик для\nдобавления\nобложки",
            image=None,
            font=ctk.CTkFont(size=10)
        )

    def change_cover(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение обложки",
            filetypes=[
                ("Изобржения", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("Все файлы", "*.*")
            ]
        )

        if file_path:
            self.game_data['cover'] = file_path
            self.load_cover()
            self.update_cover_callback()

    def play_game(self):
        self.play_callback(self.game_data)

    def delete_game(self):
        response = messagebox.askyesno(
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить '{os.path.basename(self.game_data['name'])}' из библиотеки?"
        )
        if response:
            self.delete_callback(self.game_data)

    def update_playtime_display(self, playtime_seconds):
        playtime_hours = playtime_seconds / 3600
        self.playtime_label.configure(text=f"Время игры: {playtime_hours:.1f} ч.")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Game Center")
        self.geometry("1000x600")
        self.minsize(800, 500)

        self.games_file = "games.json"
        self.games = []

        self.running_games = {}

        self.load_games()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_area()
        self.display_games()
        self.check_running_games()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=("#d1d1d1", "#1a1a1a"))
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_rowconfigure(4, weight=1)

        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="🕹️ Game Center",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.home_button = ctk.CTkButton(
            self.sidebar,
            text="🏠 Home",
            command=self.show_home,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("#c0c0c0", "#333333"),
            anchor="w"
        )
        self.home_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="⚙️ Settings",
            command=self.show_settings,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("#c0c0c0", "#333333"),
            anchor="w"
        )
        self.settings_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.games_count_label = ctk.CTkLabel(
            self.sidebar,
            text=f"Всего игр: {len(self.games)}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        self.games_count_label.grid(row=5, column=0, padx=20, pady=(0, 20))

    def create_main_area(self):
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nswe", padx=10, pady=10)
        self.main_area.grid_rowconfigure(2, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        header_label = ctk.CTkLabel(
            self.main_area,
            text="Моя библиотека игр",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        header_label.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        top_panel = ctk.CTkFrame(self.main_area, fg_color="transparent")
        top_panel.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="ew")
        top_panel.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            top_panel,
            placeholder_text="🔍 Поиск игр...",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.search_games)

        self.add_game_button = ctk.CTkButton(
            top_panel,
            text="➕ добавить игру",
            command=self.add_game,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=("#2e7d32", "#2e7d32"),
            hover_color=("#1b5e20", "#1b5e20")
        )
        self.add_game_button.grid(row=0, column=1)

        self.games_scrollable = ctk.CTkScrollableFrame(
            self.main_area,
            fg_color=("white", "#1a1a1a")
        )
        self.games_scrollable.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.games_scrollable.grid_columnconfigure(0, weight=1)
    
    def display_games(self, filter_text=""):
        for widget in self.games_scrollable.winfo_children():
            widget.destroy()

        filtered_games = self.games
        if filter_text:
            filter_text = filter_text.lower()
            filtered_games = [
                game for game in self.games
                if filter_text in game['name'].lower()
            ]

        if filtered_games:
            for idx, game in enumerate(filtered_games):
                game_card = GameCard(
                    self.games_scrollable,
                    game,
                    delete_callback=self.delete_game,
                    play_callback=self.play_game,
                    update_cover_callback=self.save_games
                )
                game_card.grid(row=idx, column=0, padx=10, pady=10, sticky="ew")
        else:
            empty_label = ctk.CTkLabel(
                self.games_scrollable,
                text="📁 Библиотека игр пуста\n\nНажмите '➕ Добавить игру', чтобы начать",
                font=ctk.CTkFont(size=16),
                text_color=("gray50", "gray70")
            )
            empty_label.grid(row=0, column=0, pady=50)

        self.games_count_label.configure(text=f"Всего игр: {len(self.games)}")
    
    def search_games(self, event=None):
        search_text = self.search_entry.get()
        self.display_games(filter_text=search_text)
    
    def add_game(self):
        file_path = filedialog.askopenfilename(
            title="Выберите исполняемый файл игры",
            filetypes=[
                ("Исполняемые файлы", "*.exe"),
                ("Все файлы", "*.*")
            ]
        )

        if file_path:
            if any(game['path'] == file_path for game in self.games):
                messagebox.showwarning("Предупреждение", "Эта игра уже добавлена в библиотеку!")
                return
            
            game_name = os.path.splitext(os.path.basename(file_path))[0]
            new_game = {
                'name': game_name,
                'path': file_path,
                'cover': '',
                'playtime': 0,
                'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        self.games.append(new_game)
        self.save_games()
        self.display_games()

        messagebox.showinfo("Успех", f"Игра '{game_name}' успешно добавлена!")

    def delete_game(self, game_data):
        self.games = [game for game in self.games if game['path'] != game_data['path']]
        self.save_games()
        self.display_games()

    def play_game(self, game_data):
        game_path = game_data['path']

        if not os.path.exists(game_path):
            messagebox.showerror(
                "Ошибка",
                f"Испольняемый файл игры не найден:\n{game_path}\n\nВозможно, игру файл был перемещен или удален."
            )
            return
        
        try:
            def run_game():
                process = subprocess.Popen([game_path])

                start_time = time.time()
                self.running_games[game_path] = {
                    'process': process,
                    'start_time': start_time,
                    'game_data': game_data
                }

                process.wait()

                end_time = time.time()
                playtime = end_time - start_time

                game_data['playtime'] = game_data.get('playtime', 0) + playtime

                if game_path in self.running_games:
                    del self.running_games[game_path]

                self.save_games()

                self.after(0, lambda: self.display_games())

            thread = threading.Thread(target=run_game, daemon=True)
            thread.start()

            messagebox.showinfo("Запуск игры", f"Игра '{game_data['name']}' запускается...")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить игру:\n{e}")

    def check_running_games(self):
        self.after(5000, self.check_running_games)
    
    def save_games(self):
        try:
            with open(self.games_file, 'w', encoding='utf-8') as f:
                json.dump(self.games, f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные:\n{str(e)}")

    def load_games(self):
        if os.path.exists(self.games_file):
            try:
                with open(self.games_file, 'r', encoding='utf-8') as f:
                    self.games = json.load(f)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{str(e)}")
                self.games = []
        else:
            self.games = []
    
    def show_home(self):
        messagebox.showinfo("Home", "Вы уже на главной странице!")
    
    def show_settings(self):
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Настройки")
        settings_window.geometry("400x300")

        title_label = ctk.CTkLabel(
            settings_window,
            text="⚙️ Настройки",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=20)

        theme_label = ctk.CTkLabel(
            settings_window,
            text="Тема интерфейса:",
            font=ctk.CTkFont(size=14)
        )
        theme_label.pack(pady=(10, 5))

        def change_theme(choice):
            ctk.set_appearance_mode(choice.lower())

        theme_menu = ctk.CTkOptionMenu(
            settings_window,
            values=["Light", "Dark", "System"],
            command=change_theme
        )
        theme_menu.set("Dark")
        theme_menu.pack(pady=5)

        info_label = ctk.CTkLabel(
            settings_window,
            text=f"Всего игр: {len(self.games)}\n"
                f"Файл данных: {self.games_file}",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        info_label.pack(pady=20)

        close_button = ctk.CTkButton(
            settings_window,
            text="Закрыть",
            command=settings_window.destroy
        )
        close_button.pack(pady=10)


def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()