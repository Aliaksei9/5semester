#include <iostream>
#include <string>
#include <vector>
#include <cmath>

#include <Windows.h>

std::string string_processing(const std::string& text) {
    if (text.size()==0) throw std::runtime_error("Вы не ввели текст");
    std::string result;
    result.reserve(text.size()); // сразу резервируем память
    
    for (unsigned char ch : text) {
        if ((static_cast<int>(ch) >= 65 and static_cast<int>(ch) <= 90) or (static_cast<int>(ch) >= 97 and static_cast<int>(ch) <= 122)) {
            result.push_back(ch);
        }
        else if (!((std::ispunct(ch)) or std::isspace(ch)))
            throw std::runtime_error("Строка должна содержать исключительно символы латиницы и знаки препинания");
    }
    return result;
}



// key = число столбцов
std::string scytale_encrypt(const std::string& plaintext, int key) {
    if (key <= 0) throw std::runtime_error("Ключ не может иметь отрицательной значение");
    if (key>= plaintext.size()) throw std::runtime_error("Слишком большой ключ");
    int n = plaintext.size();
    int cols = key;
    int rows = (n + cols - 1) / cols; // ceil

    // создаём rows x cols матрицу, заполняем пустое место #
    std::vector<std::vector<char>> mat(rows, std::vector<char>(cols, '#'));
    int idx = 0;
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            if (idx < n) mat[r][c] = plaintext[idx++];
            else mat[r][c] = 'х';
        }
    }

    // читаем по столбцам
    std::string cipher;
    cipher.reserve(rows * cols);
    for (int c = 0; c < cols; ++c) {
        for (int r = 0; r < rows; ++r) {
            cipher.push_back(mat[r][c]);
        }
    }

    return cipher;
}

std::string scytale_decrypt(const std::string& ciphertext, int key) {

    if (key <= 0)  throw std::runtime_error("Ключ не может иметь отрицательной значение");
    int n = (int)ciphertext.size();
    int cols = key;
    int rows = (n + cols - 1) / cols; 

    // заполняем матрицу по столбцам (обратный процесс)
    std::vector<std::vector<char>> mat(rows, std::vector<char>(cols, 'x'));
    int idx = 0;
    for (int c = 0; c < cols && idx < n; ++c) {
        for (int r = 0; r < rows && idx < n; ++r) {
            mat[r][c] = ciphertext[idx++];
        }
    }

    // читаем построчно
    std::string plain;
    plain.reserve(rows * cols);
    for (int r = 0; r < rows; ++r) {
        for (int c = 0; c < cols; ++c) {
            plain.push_back(mat[r][c]);
        }
    }
    //Убираем лишние знаки
    while (!plain.empty() && plain.back() == 'х') plain.pop_back();
    return plain;
}

int brute_force_attack(const std::string& ciphertext, const std::string& expected_plain) {
    int n = static_cast<int>(ciphertext.size());

    for (int cols = 1; cols < n; ++cols) {
        std::string try_plain = scytale_decrypt(ciphertext, cols);

        if (try_plain == expected_plain) {
            return cols;
        }
    }
}

// Пример использования
int main() {

    SetConsoleCP(1251);
    SetConsoleOutputCP(1251);

    std::string text;
    std::cout << "Введите текст для шифрования: ";
    std::getline(std::cin, text);

    try
    {
        text = string_processing(text);
        int key;
        std::cout << "Введите ключ (число столбцов): ";
        if (!(std::cin >> key)) return 0;

        std::string cipher = scytale_encrypt(text, key);
        std::cout << "Зашифрованный текст: " << cipher << "\n";

        std::string decrypted = scytale_decrypt(cipher, key);
        std::cout << "Расшифрованный текст: " << decrypted << "\n";

        std::cout << "Количество итераций до взлома: " << brute_force_attack(cipher, text) << "\n";
    }
    // Этот обработчик ловит std::exception и все дочерние ему классы-исключения
    catch (std::exception& exception)
    {
        std::cerr << "Исключение: " << exception.what() << '\n';
        exit(0);
    }


    return 0;
}
