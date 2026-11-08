import os
import glob

# Словарь исправлений: что было сломано -> как должно быть правильно
fixes = {
    "format_dt(%d.%m.%Y')": "format_dt('%d.%m.%Y')",
    "format_dt(%d.%m.%Y %H:%M')": "format_dt('%d.%m.%Y %H:%M')",
    "{% extends base.html %}": '{% extends "base.html" %}',
    "{% extends 'base.html' %}": '{% extends "base.html" %}',
}

print("Исправляем шаблоны...")
count = 0
# Проходим по всем HTML-файлам в папке templates
for filepath in glob.glob("templates/**/*.html", recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = content
    for bad, good in fixes.items():
        new_content = new_content.replace(bad, good)
        
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ Исправлено: {filepath}")
        count += 1

if count == 0:
    print("Все файлы уже в порядке!")
else:
    print(f"\n🎉 Готово! Исправлено файлов: {count}")