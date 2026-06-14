"""Test suite for PyJS JavaScript interpreter."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from project.interpreter import interpret


def run_js(source: str) -> list:
    return interpret(source)


class TestVisibleCases(unittest.TestCase):
    """Official hackathon visible test cases."""

    def test_odd_even_checker(self):
        source = """
let n = 7;
if (n % 2 === 0) {
    console.log("Even");
} else {
    console.log("Odd");
}
"""
        self.assertEqual(run_js(source), ["Odd"])

        source2 = """
let n = 10;
if (n % 2 === 0) {
    console.log("Even");
} else {
    console.log("Odd");
}
"""
        self.assertEqual(run_js(source2), ["Even"])

    def test_triangle_pattern(self):
        source = """
let rows = 4;
for (let i = 1; i <= rows; i++) {
    let line = "";
    for (let j = 1; j <= i; j++) {
        line = line + "*";
    }
    console.log(line);
}
"""
        expected = ["*", "**", "***", "****"]
        self.assertEqual(run_js(source), expected)

    def test_armstrong_number(self):
        source = """
function isArmstrong(num) {
    let str = String(num);
    let power = str.length;
    let sum = 0;
    for (let i = 0; i < str.length; i++) {
        let digit = Number(str[i]);
        sum = sum + Math.pow(digit, power);
    }
    return sum === num;
}

let n = 153;
if (isArmstrong(n)) {
    console.log("Armstrong");
} else {
    console.log("Not Armstrong");
}
"""
        self.assertEqual(run_js(source), ["Armstrong"])

    def test_array_reverse(self):
        source = """
let arr = [1, 2, 3, 4, 5];
let reversed = [];
for (let i = arr.length - 1; i >= 0; i--) {
    reversed.push(arr[i]);
}
console.log(reversed.join(","));
"""
        self.assertEqual(run_js(source), ["5,4,3,2,1"])

        source2 = """
let arr = [1, 2, 3, 4, 5];
arr.reverse();
console.log(arr.join(","));
"""
        self.assertEqual(run_js(source2), ["5,4,3,2,1"])

    def test_palindrome_check(self):
        source = """
function isPalindrome(str) {
    let reversed = "";
    for (let i = str.length - 1; i >= 0; i--) {
        reversed = reversed + str[i];
    }
    return str === reversed;
}

let word = "racecar";
if (isPalindrome(word)) {
    console.log("Palindrome");
} else {
    console.log("Not Palindrome");
}
"""
        self.assertEqual(run_js(source), ["Palindrome"])


class TestHiddenStyle(unittest.TestCase):
    """Hidden-style compatibility tests."""

    def test_variables_and_types(self):
        source = """
let a = 42;
const b = "hello";
var c = true;
console.log(a);
console.log(b);
console.log(c);
console.log(null);
console.log(undefined);
"""
        self.assertEqual(run_js(source), ["42", "hello", "true", "null", "undefined"])

    def test_arithmetic_and_comparison(self):
        source = """
console.log(2 + 3 * 4);
console.log(10 / 3);
console.log(10 % 3);
console.log(2 ** 8);
console.log(5 > 3);
console.log(5 === 5);
console.log(5 !== "5");
console.log(5 == "5");
"""
        self.assertEqual(
            run_js(source),
            ["14", "3.3333333333333335", "1", "256", "true", "true", "true", "true"],
        )

    def test_logical_operators(self):
        source = """
console.log(true && false);
console.log(true || false);
console.log(!false);
"""
        self.assertEqual(run_js(source), ["false", "true", "true"])

    def test_while_loop(self):
        source = """
let i = 0;
let sum = 0;
while (i < 5) {
    sum = sum + i;
    i = i + 1;
}
console.log(sum);
"""
        self.assertEqual(run_js(source), ["10"])

    def test_nested_functions(self):
        source = """
function outer(x) {
    function inner(y) {
        return x + y;
    }
    return inner(10);
}
console.log(outer(5));
"""
        self.assertEqual(run_js(source), ["15"])

    def test_arrow_functions(self):
        source = """
let add = (a, b) => a + b;
console.log(add(3, 7));
let square = (x) => x * x;
console.log(square(5));
"""
        self.assertEqual(run_js(source), ["10", "25"])

    def test_callbacks_map_filter_reduce(self):
        source = """
let nums = [1, 2, 3, 4, 5];
let doubled = nums.map(function(x) { return x * 2; });
console.log(doubled.join(","));

let evens = nums.filter(function(x) { return x % 2 === 0; });
console.log(evens.join(","));

let sum = nums.reduce(function(acc, x) { return acc + x; }, 0);
console.log(sum);
"""
        self.assertEqual(run_js(source), ["2,4,6,8,10", "2,4", "15"])

    def test_array_methods(self):
        source = """
let arr = [1, 2, 3];
arr.push(4);
console.log(arr.join("-"));
let last = arr.pop();
console.log(last);
arr.unshift(0);
console.log(arr.join("-"));
let sliced = arr.slice(1, 3);
console.log(sliced.join("-"));
"""
        self.assertEqual(run_js(source), ["1-2-3-4", "4", "0-1-2-3", "1-2"])

    def test_string_methods(self):
        source = """
let s = "  Hello World  ";
console.log(s.trim());
console.log(s.toUpperCase());
console.log(s.toLowerCase());
console.log(s.includes("World"));
console.log(s.startsWith("  H"));
console.log(s.endsWith("d  "));
console.log(s.split(" ").join("-"));
console.log(s.substring(2, 7));
console.log(s.replace("World", "JS"));
"""
        self.assertEqual(
            run_js(source),
            [
                "Hello World",
                "  HELLO WORLD  ",
                "  hello world  ",
                "true",
                "true",
                "true",
                "--Hello-World--",
                "Hello",
                "  Hello JS  ",
            ],
        )

    def test_objects(self):
        source = """
let person = { name: "Alice", age: 30 };
console.log(person.name);
person.age = 31;
console.log(person.age);
let nested = { data: { value: 42 } };
console.log(nested.data.value);
"""
        self.assertEqual(run_js(source), ["Alice", "31", "42"])

    def test_math(self):
        source = """
console.log(Math.floor(3.7));
console.log(Math.ceil(3.2));
console.log(Math.round(3.5));
console.log(Math.abs(-5));
console.log(Math.pow(2, 10));
console.log(Math.max(1, 5, 3));
console.log(Math.min(1, 5, 3));
"""
        self.assertEqual(run_js(source), ["3", "4", "4", "5", "1024", "5", "1"])

    def test_type_conversion(self):
        source = """
console.log(String(123));
console.log(Number("456"));
console.log(Boolean(0));
console.log(Boolean(1));
console.log(Boolean(""));
"""
        self.assertEqual(run_js(source), ["123", "456", "false", "true", "false"])

    def test_spread_and_rest(self):
        source = """
let a = [1, 2];
let b = [...a, 3, 4];
console.log(b.join(","));

function sum(...args) {
    let total = 0;
    for (let i = 0; i < args.length; i++) {
        total = total + args[i];
    }
    return total;
}
console.log(sum(1, 2, 3, 4));
"""
        self.assertEqual(run_js(source), ["1,2,3,4", "10"])

    def test_nested_loops(self):
        source = """
let result = "";
for (let i = 0; i < 2; i++) {
    for (let j = 0; j < 2; j++) {
        result = result + i + "" + j + " ";
    }
}
console.log(result.trim());
"""
        self.assertEqual(run_js(source), ["00 01 10 11"])

    def test_recursion(self):
        source = """
function factorial(n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}
console.log(factorial(5));
"""
        self.assertEqual(run_js(source), ["120"])

    def test_array_chaining(self):
        source = """
let result = [1, 2, 3, 4, 5]
    .filter(function(x) { return x % 2 === 0; })
    .map(function(x) { return x * 10; })
    .reduce(function(a, b) { return a + b; }, 0);
console.log(result);
"""
        self.assertEqual(run_js(source), ["60"])

    def test_increment_decrement(self):
        source = """
let x = 5;
console.log(x++);
console.log(x);
console.log(++x);
console.log(x);
"""
        self.assertEqual(run_js(source), ["5", "6", "7", "7"])


if __name__ == "__main__":
    unittest.main()
