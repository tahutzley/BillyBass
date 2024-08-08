class Config:
    current_voice = "Davis"
    current_style = "Shouting"
    current_music_stream = False
    is_listening = False
    is_speaking = False

    def update_voice(self, voice):
        self.current_voice = voice

    def update_style(self, style):
        self.current_style = style

    def update_music_stream(self, is_active):
        self.current_music_stream = is_active

    def update_is_listening(self, is_listening):
            self.is_listening = is_listening

    def update_is_speaking(self, is_speaking):
                self.is_speaking = is_speaking
