#include <iostream>
#include <vector>
#include <map>
#include <cstdlib>   // rand, srand
#include <ctime>     // time
#include <iomanip>   // setw
#include <cmath>

using namespace std;

// Генерация случайной строки из символов алфавита
string generateString(int length, const string& alphabet) {
    string result;
    result.reserve(length);
    int n = alphabet.size();
    int charachter_code;
    for (int i = 0; i < length; ++i)
    {
        charachter_code = rand() % n;
        result.push_back(alphabet[charachter_code]);
    }
    return result;
}

// Подсчет частот символов
map<char, int> countFrequency(const string& str, const string& alphabet) {
    map<char, int> freq;
    for (char c : alphabet) freq[c] = 0;  // инициализируем
    for (char c : str) freq[c]++;
    return freq;
}

// Визуализация частот (гистограмма)
void visualizeHistogram(const map<char, int>& freq) {
    cout << "\nЧастотное распределение символов:\n";
    for (auto& p : freq) {
        cout << p.first << " | " << setw(5) << p.second << " | ";
        for (int i = 0; i < p.second; i++)
            cout << "#";
        cout << "\n";
    }
}

int hackingTimeCalculate(int length, const string& alphabet)
{
    int n = alphabet.size();
    long time = pow(alphabet.size(), length) / 127240.671;
    return time;
}

int main() {
    setlocale(LC_ALL, "Russian");

    srand(static_cast<unsigned int>(time(0)));

    int length;
    cout << "Введите длину строки: ";
    cin >> length;
    string alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

    string randomStr = generateString(length, alphabet);

    cout << "\nСгенерированная строка:\n" << randomStr << "\n";
    cout << "\nВремя взлома:\n" << hackingTimeCalculate(length, alphabet) << "\n";
    auto freq = countFrequency(randomStr, alphabet);
    visualizeHistogram(freq);

    return 0;
}
