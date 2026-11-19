# calc: spec extraída de `legacy/calc.py`

## Contrato de E/S
- stdin: una expresión por línea (UTF-8).
- stdout: por cada línea, exactamente una línea: `ok <entero>` o `err <tipo>`.
- Tipos de error: `parse`, `div0`, `negexp`, `toobig`, `crash`.

## Pseudocódigo
```
evaluate(line):
  toks = tokenize(line)            # un error de tokenización gana a todo
  v = expr()
  si sobran tokens -> err parse

tokenize:
  espacio (str.isspace, unicode)  -> se salta
  racha de dígitos (str.isdigit)  -> int(racha)
  uno de + - * / % ^ ( )          -> operador
  cualquier otro carácter         -> err parse

expr  := term (('+' | '-') term)*         asociativo a la izquierda
term  := unary (('*' | '/' | '%') unary)* izquierda; el operando derecho se evalúa
                                          ANTES de mirar si es cero
           '/' = división piso (redondea hacia -inf): -7/2 = -4, 7/-2 = -4
           '%' = resto con el signo del divisor:      7%-2 = -1, -7%2 = 1
           divisor 0 -> err div0
unary := '-' unary | power                -2^2 = -4 (el menos envuelve a la potencia)
power := atom ('^' unary)?                derecha: 2^3^2 = 512
           exponente < 0 -> err negexp; > 1000 -> err toobig
atom  := entero | '(' expr ')'            otra cosa -> err parse
```
Evaluación ansiosa de izquierda a derecha: gana el primer error que aparece.
`(1/0` -> `div0` (no `parse`). `1/0 $` -> `parse` (tokenize va primero).

## Quirks del original (comportamiento observado, no intencional)
- Enteros sin límite (`9999^1000` imprime ~4000 dígitos).
- `str()` de un entero de más de 4300 dígitos lanza ValueError -> `err crash`.
- `isdigit` acepta dígitos unicode: `٣+1` -> `ok 4`; `²` pasa `isdigit` pero `int()` falla -> `err crash`.
- Recursión: el original revienta (`err crash`) al pasar de 1000 frames de Python.
  Medido: 198 paréntesis anidados ok, 199 crash; 990 `-` seguidos ok, 991 crash.
  Cada nivel de paréntesis cuesta 5 frames (expr, term, unary, power, atom); cada `-` cuesta 1.
  La base son 3 frames (módulo, main, evaluate) más 2 al fondo (atom -> take -> peek).
- No hay `+` unario: `+1` -> `parse`. Línea vacía -> `parse`.

## Decisiones para el port a Rust (revisión humana)
- Enteros `i64`. Cualquier resultado o literal fuera de rango -> `err overflow`.
  Divergencia aceptada solo si el original dio un entero fuera de i64 o `crash` (ver `accept.py`).
- Dígitos: solo ASCII. Una línea con dígitos no ASCII puede dar `err parse` en Rust; divergencia aceptada.
- Recursión: se emula el contador de frames del original para dar `crash` en el mismo punto.
