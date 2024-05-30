import json
import os

def generate_music_notes():
    folder_name = "score/score"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    file_name = input("请输入乐谱名称：")
    time = float(input("请输入时间："))
    music_notes = []
    while True:
        user_input = input("请输入字母：")
        if user_input == "exit":
            break
        if len(user_input) == 1:
            music_notes.append({"key": user_input, "time": time})
        else:
            music_notes.append({"key": list(user_input), "time": time})
            
    file_path = os.path.join(folder_name, f"{file_name}.json")
    with open(file_path, "w") as file:
        json.dump(music_notes, file)

generate_music_notes()
