// Palindrome Check
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
