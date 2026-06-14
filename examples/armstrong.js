// Armstrong Number
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
