#!/usr/bin/env python3
"""
Скрипт для добавления кнопки выплаты в keyboards.py
"""

# Читаем файл
with open('core/keyboards.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Ищем нужное место для вставки
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    
    # Ищем закрывающую скобку перед "Назад в меню" в profile_keyboard
    if '# Показываем кнопку "Привязать YouTube" только если YouTube не привязан' in line:
        # Следующие 4 строки - это блок YouTube
        for j in range(4):
            i += 1
            new_lines.append(lines[i])
        
        # Вставляем новый блок
        new_lines.append('    \n')
        new_lines.append('    # Показываем кнопку "Запросить выплату" если баланс > 0\n')
        new_lines.append('    if balance > 0:\n')
        new_lines.append('        builder.row(\n')
        new_lines.append('            InlineKeyboardButton(text="💸 Запросить выплату", callback_data="request_balance_payout")\n')
        new_lines.append('        )\n')
    
    i += 1

# Записываем обратно
with open('core/keyboards.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Файл keyboards.py успешно исправлен!")
