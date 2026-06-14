# PyJS — Build Your Own JavaScript

A from-scratch JavaScript interpreter written in **Python** for Thunder Hackathon 2.0.

PyJS accepts JavaScript source code, tokenizes it, builds an AST, and executes it using a tree-walking interpreter — **no Node.js, no subprocess, no external JS runtime**.

## Architecture

```
JavaScript Source
       ↓
    Lexer (lexer.py)
       ↓
    Tokens
       ↓
    Parser (parser.py)
       ↓
    AST (ast_nodes.py)
       ↓
    Interpreter (interpreter.py)
       ↓
    Output (console.log)
```

### Pipeline Components

| Module | Purpose |
|--------|---------|
| `lexer.py` | Tokenizes JS source (keywords, operators, literals, comments) |
| `parser.py` | Recursive-descent parser producing an AST |
| `ast_nodes.py` | AST node definitions |
| `interpreter.py` | Tree-walking evaluator |
| `environment.py` | Lexical scope chain (`let` / `const` / `var`) |
| `runtime.py` | JS value types and coercion rules |
| `builtins.py` | `console`, `Math`, `Date`, array/string methods |
| `errors.py` | Lexer, parser, and runtime errors |

## Supported Features

### Variables
- `let`, `const`, `var`
- Block scoping and shadowing
- `const` assignment protection

### Types
- `number`, `string`, `boolean`, `null`, `undefined`
- Arrays and objects
- Functions (declarations, expressions, arrows)

### Operators
- Arithmetic: `+`, `-`, `*`, `/`, `%`, `**`
- Comparison: `==`, `===`, `!=`, `!==`, `<`, `<=`, `>`, `>=`
- Logical: `&&`, `||`, `!`
- Assignment: `=`, `+=`, `-=`, `*=`, `/=`, `%=`
- Update: `++`, `--`

### Control Flow
- `if` / `else` / `else if`
- `for`, `while`
- `return`

### Functions
- Function declarations and expressions
- Arrow functions `(a, b) => a + b` and `x => x * 2`
- Closures and recursion
- Rest parameters `(...args)`

### Arrays
- `length`, `push`, `pop`, `shift`, `unshift`
- `slice`, `splice`, `reverse`, `join`
- `map`, `filter`, `reduce`, `forEach`
- Spread: `[...arr]`

### Strings
- `length`, `split`, `slice`, `substring`, `replace`
- `includes`, `startsWith`, `endsWith`
- `trim`, `toUpperCase`, `toLowerCase`

### Objects
- Object literals `{ key: value }`
- Dot and bracket property access
- Nested objects

### Built-ins
- `console.log()` with JS-style formatting
- `Math.floor`, `Math.ceil`, `Math.round`, `Math.abs`, `Math.pow`, `Math.max`, `Math.min`, `Math.random`
- `Date` constructor and `Date.now()`
- `String()`, `Number()`, `Boolean()`

## How To Run

```bash
# Run a JavaScript file
python project/main.py examples/odd_even.js

# Execute inline code
python project/main.py -e "console.log(2 + 2);"

# Pipe from stdin
echo "console.log('Hello');" | python project/main.py
```

## How To Test

```bash
python -m unittest tests.test_interpreter -v
```

## Example Inputs & Outputs

### Odd / Even
```javascript
let n = 7;
if (n % 2 === 0) console.log("Even");
else console.log("Odd");
```
**Output:** `Odd`

### Triangle Pattern
```javascript
for (let i = 1; i <= 4; i++) {
    let line = "";
    for (let j = 1; j <= i; j++) line = line + "*";
    console.log(line);
}
```
**Output:**
```
*
**
***
****
```

### Armstrong Number
```javascript
function isArmstrong(num) {
    let str = String(num);
    let sum = 0;
    for (let i = 0; i < str.length; i++)
        sum += Math.pow(Number(str[i]), str.length);
    return sum === num;
}
console.log(isArmstrong(153) ? "Armstrong" : "Not Armstrong");
```
**Output:** `Armstrong`

## Implementation Details

- **Lexer**: Single-pass scanner with support for `//` and `/* */` comments, hex numbers, and string escape sequences.
- **Parser**: Recursive descent with operator precedence climbing for expressions.
- **Environment**: Chain of scope frames; `let`/`const` are block-scoped, `var` is function-scoped.
- **Runtime values**: Distinct Python classes mirror JS types with proper truthiness and coercion.
- **console.log**: Formats `true`/`false`/`null`/`undefined`, arrays as `[1, 2, 3]`, objects as `[object Object]`.

## Future Improvements

- Full `===` object structural equality
- `try` / `catch` / `throw`
- Template literals and destructuring
- `class` syntax
- `switch` / `break` / `continue`
- Prototype-based inheritance
- Bytecode compiler + VM for performance
- Source maps for better error messages

## Project Structure

```
project/
├── main.py           # CLI entry point
├── lexer.py          # Tokenizer
├── parser.py         # Parser
├── ast_nodes.py      # AST definitions
├── interpreter.py    # Evaluator
├── environment.py    # Scope chain
├── runtime.py        # JS value types
├── builtins.py       # Native objects/methods
└── errors.py         # Error types
tests/
└── test_interpreter.py
examples/
├── odd_even.js
├── triangle.js
├── armstrong.js
├── array_reverse.js
└── palindrome.js
```

## License

Built for Thunder Hackathon 2.0.
