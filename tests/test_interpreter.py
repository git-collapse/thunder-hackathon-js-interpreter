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


class TestHiddenHardening(unittest.TestCase):
    """Regression tests for likely hidden-test language features."""

    def test_break_continue_nested_loops(self):
        source = """
let result = "";
for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 4; j++) {
        if (j === 1) continue;
        if (j === 3) break;
        result += i + ":" + j + ";";
    }
}
console.log(result);
"""
        self.assertEqual(run_js(source), ["0:0;0:2;1:0;1:2;2:0;2:2;"])

    def test_switch_case_default_and_fallthrough(self):
        source = """
let value = 2;
let result = "";
switch (value) {
    case 1:
        result += "one";
        break;
    case 2:
        result += "two";
    case 3:
        result += "-three";
        break;
    default:
        result += "default";
}
console.log(result);

switch ("x") {
    case "y":
        console.log("bad");
        break;
    default:
        console.log("fallback");
}
"""
        self.assertEqual(run_js(source), ["two-three", "fallback"])

    def test_ternary_typeof_and_template_literals(self):
        source = """
let n = 4;
console.log(n % 2 === 0 ? "even" : "odd");
console.log(typeof n);
console.log(typeof missing);
console.log(typeof console.log);
console.log(`n=${n}, next=${n + 1}`);
"""
        self.assertEqual(
            run_js(source),
            ["even", "number", "undefined", "function", "n=4, next=5"],
        )

    def test_for_of_and_for_in(self):
        source = """
let total = 0;
for (let value of [1, 2, 3]) {
    total += value;
}
console.log(total);

let keys = "";
let obj = { a: 1, b: 2 };
for (let key in obj) {
    keys += key;
}
console.log(keys);

for (var index in [9, 8]) {
}
console.log(index);
"""
        self.assertEqual(run_js(source), ["6", "ab", "1"])

    def test_string_required_edge_methods(self):
        source = """
let s = "abcabc";
console.log(s.indexOf("b"));
console.log(s.lastIndexOf("b"));
console.log(s.charAt(2));
console.log(s.charCodeAt(0));
console.log("x".repeat(3));
console.log("7".padStart(3, "0"));
console.log("7".padEnd(3, "0"));
"""
        self.assertEqual(run_js(source), ["1", "4", "c", "97", "xxx", "007", "700"])

    def test_var_hoisting_and_scope_shadowing(self):
        source = """
console.log(x);
var x = 1;
if (true) {
    var x = 2;
    let shadow = "inner";
    console.log(shadow);
}
let shadow = "outer";
console.log(x);
console.log(shadow);
"""
        self.assertEqual(run_js(source), ["undefined", "inner", "2", "outer"])

    def test_callback_chain_and_array_mutation(self):
        source = """
let arr = [1, 2, 3];
let seen = [];
arr.forEach(function(x, index) {
    seen.push(x);
    if (index === 0) arr.push(4);
});
console.log(seen.join(","));
console.log(arr.join(","));

let result = arr
    .filter(function(x) { return x % 2 === 0; })
    .map(function(x) { return x * 3; })
    .reduce(function(acc, x) { return acc + x; }, 0);
console.log(result);
"""
        self.assertEqual(run_js(source), ["1,2,3", "1,2,3,4", "18"])

    def test_date_now_and_get_time(self):
        source = """
console.log(Date.now() > 0);
let d = new Date(0);
console.log(d.getTime());
"""
        self.assertEqual(run_js(source), ["true", "0"])

    def test_array_destructuring_declarations_and_assignment(self):
        source = """
let arr = [1, 2, 3];
let [a, b] = arr;
console.log(a, b);

let [head, ...tail] = arr;
console.log(head, tail.join(","));

let [, second, third] = arr;
console.log(second, third);

let x = 0;
let y = 0;
[x, y] = [4, 5];
console.log(x, y);
"""
        self.assertEqual(run_js(source), ["1 2", "1 2,3", "2 3", "4 5"])

    def test_try_catch_throw_and_finally(self):
        source = """
try {
    throw "boom";
} catch (err) {
    console.log(err);
}

let trace = "";
try {
    trace += "try";
} finally {
    trace += "-finally";
}
console.log(trace);

try {
    throw [7, 8];
} catch ([a, b]) {
    console.log(a, b);
}

try {
    missingValue;
} catch (err) {
    console.log(err.includes("Undefined variable"));
}
"""
        self.assertEqual(run_js(source), ["boom", "try-finally", "7 8", "true"])


if __name__ == "__main__":
    unittest.main()
