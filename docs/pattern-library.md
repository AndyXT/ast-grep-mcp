# AST-Grep Pattern Library

This document provides a comprehensive reference of all available AST patterns in the ast-grep-mcp library. Each language section includes examples and explanations for:

- Basic code constructs
- Anti-patterns and code smells
- Performance optimization patterns
- Security vulnerability patterns
- Refactoring patterns

## Table of Contents

- [Python Patterns](#python-patterns)
- [JavaScript Patterns](#javascript-patterns)
- [TypeScript Patterns](#typescript-patterns)
- [Rust Patterns](#rust-patterns)
- [Go Patterns](#go-patterns)
- [C Patterns](#c-patterns)

## Pattern Syntax Reference

AST-grep uses a powerful pattern matching syntax:

- `$NAME` - Matches a single node (variable, identifier, etc.)
- `$$$PARAMS` - Matches multiple nodes (zero or more)
- `$_` - Wildcard that matches any single node
- `$...` - Matches a specific node type

## Python Patterns

### Basic Code Constructs

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `function_definition` | Match function definitions | `def $NAME($$$PARAMS):` | `def calculate_total(price, tax):` |
| `class_definition` | Match class definitions | `class $NAME:` | `class User:` |
| `method_definition` | Match method definitions | `def $NAME(self, $$$PARAMS):` | `def save(self, force=False):` |
| `for_loop` | Match for loops | `for $VAR in $ITERABLE:` | `for item in items:` |
| `with_statement` | Match with statements | `with $CONTEXT as $VAR:` | `with open('file.txt') as f:` |
| `lambda` | Match lambda expressions | `lambda $$$PARAMS: $EXPR` | `lambda x, y: x + y` |

### Anti-Patterns and Code Smells

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `bare_except` | Match bare except blocks | `try:\n    $$$BODY\nexcept:\n    $$$HANDLER` | `try:\n    do_something()\nexcept:\n    pass` |
| `except_pass` | Match except blocks with pass | `try:\n    $$$BODY\nexcept $EXCEPTION:\n    pass` | `try:\n    db.connect()\nexcept ConnectionError:\n    pass` |
| `mutable_default_arg` | Match functions with mutable default arguments | `def $NAME($PARAM=$MUTABLE_VALUE):` | `def add_item(item, items=[]):` |
| `global_statement` | Match global statements | `global $NAME` | `global counter` |
| `nested_loops` | Match nested loops | `for $OUTER_VAR in $OUTER_ITER:\n    for $INNER_VAR in $INNER_ITER:\n        $$$BODY` | `for user in users:\n    for role in user.roles:\n        print(role)` |

### Performance Optimizations

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `list_in_loop` | Match inefficient list building | `for $VAR in $ITER:\n    $$$BODY\n    $LIST.append($ITEM)` | `for i in range(1000):\n    results.append(i*2)` |
| `string_concat_in_loop` | Match inefficient string concatenation | `for $VAR in $ITER:\n    $STR += $SOMETHING` | `for word in words:\n    message += word` |
| `inefficient_dict_lookup` | Match inefficient dictionary lookups | `$DICT[$KEY] if $KEY in $DICT else $DEFAULT` | `user_data[user_id] if user_id in user_data else {}` |
| `repeated_calculation` | Match repeated expensive calculations | `for $VAR in $ITER:\n    $$$BODY\n    $EXPENSIVE_FUNC($ARGS)` | `for item in items:\n    process(item, calculate_complex_value())` |

### Security Vulnerabilities

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `eval_call` | Match dangerous eval calls | `eval($EXPR)` | `eval(user_input)` |
| `exec_call` | Match dangerous exec calls | `exec($CODE)` | `exec(code_from_user)` |
| `shell_true` | Match subprocess with shell=True | `subprocess.run($CMD, shell=True)` | `subprocess.run(user_cmd, shell=True)` |
| `sql_format` | Match potential SQL injection | `cursor.execute(f"$$$SQL {$USER_INPUT}")` | `cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")` |
| `pickle_load` | Match insecure pickle loading | `pickle.load($FILE)` | `data = pickle.load(untrusted_file)` |

### Refactoring Patterns

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `if_return_early` | Match early return patterns | `if $COND:\n    return $EARLY\n$$$MORE_CODE\nreturn $LATE` | `if not valid:\n    return None\n# process data\nreturn result` |
| `dict_get_with_default` | Match inefficient dictionary get | `if $KEY in $DICT:\n    $VAR = $DICT[$KEY]\nelse:\n    $VAR = $DEFAULT` | `if 'user' in data:\n    user = data['user']\nelse:\n    user = None` |
| `explicit_none_compare` | Match explicit None comparisons | `if $VAR == None:` | `if result == None:` |
| `redundant_with_open` | Match redundant file operations | `with open($FILE, $MODE) as $F:\n    $CONTENT = $F.read()\n    $$$OPERATIONS_ON_CONTENT` | `with open('data.txt', 'r') as f:\n    content = f.read()\n    process_content(content)` |

## JavaScript Patterns

### Basic Code Constructs

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `function_declaration` | Match function declarations | `function $NAME($$$PARAMS) { $$$BODY }` | `function calculateTotal(price, tax) { return price * (1 + tax); }` |
| `arrow_function` | Match arrow functions | `($$$PARAMS) => $$$BODY` | `(x, y) => x + y` |
| `class_declaration` | Match class declarations | `class $NAME { $$$BODY }` | `class User { constructor(name) { this.name = name; } }` |
| `method_definition` | Match method definitions | `$NAME($$$PARAMS) { $$$BODY }` | `save(force) { this.repository.save(this, force); }` |
| `destructuring_assignment` | Match destructuring | `const { $$$PROPS } = $OBJ` | `const { name, age } = user;` |
| `template_literal` | Match template literals | \``$$$EXPR`\` | \``Hello ${userName}`\` |

### Anti-Patterns and Code Smells

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `var_declaration` | Match var declarations | `var $NAME = $VALUE` | `var count = 0;` |
| `with_statement` | Match with statements | `with ($OBJ) { $$$BODY }` | `with (document) { write('Hello'); }` |
| `alert` | Match alert calls | `alert($MESSAGE)` | `alert('Warning');` |
| `document_write` | Match document.write | `document.write($CONTENT)` | `document.write('<p>Content</p>');` |
| `nested_callbacks` | Match nested callbacks | `$FUNC($$$ARGS, function($$$PARAMS) { $$$BODY })` | `fetchData(url, function(data) { processData(data); });` |

### Performance Optimizations

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `array_push_in_loop` | Match array push in loop | `for ($$$INIT) { $ARR.push($ITEM) }` | `for (let i = 0; i < 1000; i++) { results.push(i*2); }` |
| `inefficient_dom_query` | Match inefficient DOM queries | `document.querySelectorAll($SELECTOR)` | `const items = document.querySelectorAll('.item');` |
| `innerHTML_in_loop` | Match innerHTML in loop | `for ($$$INIT) { $ELEM.innerHTML += $CONTENT }` | `for (const item of items) { container.innerHTML += item.html; }` |
| `blocking_event_handler` | Match blocking event handlers | `$ELEM.addEventListener('$EVENT', function() { $$$HEAVY_COMPUTATION })` | `button.addEventListener('click', function() { processLargeDataset(); });` |

### Security Vulnerabilities

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `eval_call` | Match eval calls | `eval($CODE)` | `eval(userInput);` |
| `innerHTML_user_input` | Match innerHTML with user input | `$ELEM.innerHTML = $USER_INPUT` | `element.innerHTML = message;` |
| `document_location_href` | Match location assignments | `document.location.href = $USER_INPUT` | `document.location.href = redirectUrl;` |
| `dangerouslySetInnerHTML` | Match React dangerouslySetInnerHTML | `dangerouslySetInnerHTML={{ __html: $USER_INPUT }}` | `<div dangerouslySetInnerHTML={{ __html: content }} />` |

## TypeScript Patterns

In addition to all JavaScript patterns, TypeScript includes:

### Basic TypeScript Patterns

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `interface_declaration` | Match interface declarations | `interface $NAME { $$$BODY }` | `interface User { id: number; name: string; }` |
| `type_declaration` | Match type declarations | `type $NAME = $TYPE` | `type ID = string | number;` |
| `typed_function` | Match typed functions | `function $NAME($$$PARAMS): $RETURN_TYPE { $$$BODY }` | `function sum(a: number, b: number): number { return a + b; }` |
| `generic_type` | Match generic types | `$NAME<$$$TYPE_PARAMS>` | `Array<string>` |

### Anti-Patterns and Code Smells

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `any_type` | Match any type usage | `: any` | `function process(data: any) { }` |
| `non_null_assertion` | Match non-null assertions | `$EXPR!` | `user!.profile.address` |
| `type_assertion_any` | Match cast to any | `$EXPR as any` | `(obj as any).invalidMethod()` |
| `complex_union` | Match complex union types | `$TYPE1 \| $TYPE2 \| $TYPE3 \| $TYPE4` | `type Response = string \| number \| boolean \| object \| null;` |

### Refactoring Patterns

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `optional_chain` | Match optional chaining | `$OBJ?.$PROP` | `user?.address?.street` |
| `nullish_coalescing` | Match nullish coalescing | `$EXPR ?? $DEFAULT` | `const name = userName ?? 'Guest';` |
| `type_guard` | Match type guards | `function is$TYPE($PARAM: any): $PARAM is $TYPE { $$$BODY }` | `function isUser(obj: any): obj is User { return 'id' in obj; }` |
| `keyof_operator` | Match keyof operator | `keyof $TYPE` | `type UserKeys = keyof User;` |

## Rust Patterns

### Basic Code Constructs

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `function` | Match function definitions | `fn $NAME($$$PARAMS) -> $RET_TYPE` | `fn calculate_tax(amount: f64) -> f64` |
| `struct` | Match struct definitions | `struct $NAME { $$$FIELDS }` | `struct User { id: u64, name: String }` |
| `enum` | Match enum definitions | `enum $NAME { $$$VARIANTS }` | `enum Status { Active, Inactive, Pending }` |
| `impl` | Match impl blocks | `impl $NAME { $$$METHODS }` | `impl User { fn new(name: &str) -> Self { ... } }` |
| `trait` | Match trait definitions | `trait $NAME { $$$METHODS }` | `trait Drawable { fn draw(&self); }` |
| `macro_invocation` | Match macro invocations | `$NAME!($$$ARGS)` | `println!("Hello, {}", name)` |

### Anti-Patterns and Code Smells

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `unwrap` | Match unwrap calls | `$EXPR.unwrap()` | `result.unwrap()` |
| `expect` | Match expect calls | `$EXPR.expect($MESSAGE)` | `file.expect("Failed to open file")` |
| `clone_in_loop` | Match clone in loops | `for $VAR in $ITER { $$$_; $EXPR.clone(); $$$_ }` | `for user in users { names.push(user.name.clone()); }` |
| `nested_match` | Match nested match statements | `match $EXPR { $$$_; match $INNER_EXPR { $$$_ } $$$_ }` | `match result { Ok(value) => match value { ... } }` |
| `needless_return` | Match unnecessary return | `return $EXPR;` | `return some_value;` |

### Performance Optimizations

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `box_vec_new` | Match boxed vectors | `Box::new(vec![$$$ITEMS])` | `Box::new(vec![1, 2, 3])` |
| `string_add_push_str` | Match string addition | `$STRING = $STRING + $OTHER` | `s = s + "world"` |
| `redundant_clone` | Match unnecessary clones | `$VAR.clone()` | `let copy = original.clone();` |
| `unnecessary_sort_by` | Match default sort implementation | `$VEC.sort_by(\|a, b\| a.cmp(b))` | `numbers.sort_by(|a, b| a.cmp(b))` |
| `inefficient_iterator_chain` | Match inefficient iterator chains | `$ITER.collect::<Vec<_>>().$$$METHOD()` | `items.collect::<Vec<_>>().iter().map(|x| x * 2)` |

### Security Vulnerabilities

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `dangerous_transmute` | Match transmute calls | `std::mem::transmute::<$FROM, $TO>($EXPR)` | `std::mem::transmute::<*const u8, *const i32>(ptr)` |
| `unsafe_code_block` | Match unsafe blocks | `unsafe { $$$CODE }` | `unsafe { *ptr = 42; }` |
| `raw_pointer_deref` | Match raw pointer dereferences | `*$PTR` | `let value = *raw_ptr;` |
| `format_string_injection` | Match format string issues | `format!($USER_INPUT, $$$ARGS)` | `format!(user_pattern, value1, value2)` |

### Refactoring Patterns

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `if_let_chain` | Match if-let chains | `if let $PATTERN1 = $EXPR1 { if let $PATTERN2 = $EXPR2 { $$$CODE } }` | `if let Some(user) = get_user() { if let Some(addr) = user.address { ... } }` |
| `match_to_if_let` | Match simple match statements | `match $EXPR { $PATTERN => $BLOCK, _ => $DEFAULT }` | `match result { Ok(value) => process(value), _ => default() }` |
| `explicit_deref` | Match redundant dereferences | `*(&$EXPR)` | `let value = *(&some_var);` |
| `bool_comparison` | Match explicit bool comparisons | `if $EXPR == true` | `if is_valid == true { ... }` |
| `mutex_guard` | Match mutex lock patterns | `let $GUARD = $MUTEX.lock().unwrap(); $$$CODE` | `let data = mutex.lock().unwrap(); process(data);` |

## Go Patterns

### Basic Code Constructs

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `function` | Match function definitions | `func $NAME($$$PARAMS) $$$RETURN_TYPE` | `func ProcessOrder(id int, options ...Option) error` |
| `struct` | Match struct definitions | `type $NAME struct { $$$FIELDS }` | `type User struct { ID int; Name string }` |
| `interface` | Match interface definitions | `type $NAME interface { $$$METHODS }` | `type Reader interface { Read(p []byte) (n int, err error) }` |
| `method` | Match method definitions | `func ($RECEIVER $TYPE) $NAME($$$PARAMS) $$$RETURN_TYPE` | `func (u *User) Save() error` |
| `import` | Match import statements | `import ($$$IMPORTS)` | `import ("fmt"; "strings")` |
| `range_loop` | Match range loops | `for $KEY, $VALUE := range $COLLECTION { $$$BODY }` | `for i, item := range items { fmt.Println(i, item) }` |

### Anti-Patterns and Code Smells

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `naked_return` | Match naked returns | `return` | `func getValue() (result int) { result = 42; return }` |
| `empty_interface_param` | Match empty interface parameters | `func $NAME($PARAM interface{}) $$$RETURN_TYPE` | `func Process(data interface{}) error` |
| `panic_call` | Match panic calls | `panic($MESSAGE)` | `panic("unexpected error")` |
| `goroutine_without_sync` | Match unsynchronized goroutines | `go func() { $$$BODY }()` | `go func() { processData() }()` |
| `bool_param_leading` | Match leading boolean parameters | `func $NAME($FLAG bool, $$$OTHER_PARAMS)` | `func SendEmail(force bool, message string)` |

### Performance Optimizations

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `string_concat_plus` | Match string concatenation | `$STR = $STR + $OTHER` | `message = message + " world"` |
| `inefficient_slice_append` | Match inefficient slice appending | `for $_, $ELEM := range $SOURCE { $DEST = append($DEST, $ELEM) }` | `for _, num := range source { dest = append(dest, num) }` |
| `unnecessary_allocation` | Match unnecessary allocations | `make([]$TYPE, 0)` | `users := make([]User, 0)` |
| `map_without_capacity` | Match maps without capacity | `make(map[$KEY]$VALUE)` | `cache := make(map[string]int)` |
| `mutex_copy` | Match mutex copying | `var $NEW_MUT $MUT` | `var newMutex sync.Mutex = oldMutex` |

### Security Vulnerabilities

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `sql_injection` | Match SQL injection patterns | `db.Exec($QUERY + $USER_INPUT)` | `db.Exec("SELECT * FROM users WHERE id = " + userID)` |
| `command_injection` | Match command injection | `exec.Command("sh", "-c", $USER_INPUT)` | `exec.Command("sh", "-c", userCommand)` |
| `weak_rand` | Match insecure random number generation | `rand.Intn($NUM)` | `randomNum := rand.Intn(100)` |
| `insecure_temp_file` | Match insecure temp file creation | `ioutil.TempFile("", $PREFIX)` | `file, _ := ioutil.TempFile("", "prefix")` |
| `http_redirect_open` | Match open redirects | `http.Redirect($W, $R, $LOCATION, http.StatusFound)` | `http.Redirect(w, r, redirect, http.StatusFound)` |

### Refactoring Patterns

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `nil_check` | Match nil checks | `if $VAR == nil { $$$ERROR_HANDLING }` | `if result == nil { return errors.New("not found") }` |
| `error_check` | Match error checks | `if err != nil { $$$ERROR_HANDLING }` | `if err != nil { log.Fatal(err) }` |
| `nested_if` | Match nested if statements | `if $COND1 { if $COND2 { $$$BODY } }` | `if user != nil { if user.IsAdmin { doAdminStuff() } }` |
| `explicit_type_conversion` | Match explicit type conversions | `$TYPE($VAR)` | `float64(count)` |
| `map_value_check` | Match map checks | `if $VAL, $OK := $MAP[$KEY]; $OK { $$$BODY }` | `if val, ok := cache[key]; ok { return val, nil }` |

## C Patterns

### Basic Code Constructs

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `function` | Match function definitions | `$RET_TYPE $NAME($$$PARAMS)` | `int calculate_sum(int a, int b)` |
| `struct` | Match struct definitions | `struct $NAME { $$$FIELDS }` | `struct User { int id; char* name; };` |
| `enum` | Match enum definitions | `enum $NAME { $$$VALUES }` | `enum Color { RED, GREEN, BLUE };` |
| `typedef` | Match typedef statements | `typedef $OLD_TYPE $NEW_TYPE;` | `typedef unsigned long size_t;` |
| `macro` | Match macro definitions | `#define $NAME($$$PARAMS) $BODY` | `#define MAX(a, b) ((a) > (b) ? (a) : (b))` |
| `include` | Match include statements | `#include $HEADER` | `#include <stdio.h>` |

### Anti-Patterns and Code Smells

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `goto` | Match goto statements | `goto $LABEL;` | `goto error;` |
| `magic_number` | Match magic numbers | `$EXPR $OP $NUMBER` | `if (age > 18) { /* ... */ }` |
| `nested_conditional` | Match nested conditionals | `if ($COND1) { if ($COND2) { $$$BODY } }` | `if (user) { if (user->is_admin) { /* ... */ } }` |
| `global_var` | Match global variables | `$TYPE $NAME = $VALUE;` | `int counter = 0;` |
| `deeply_nested_loop` | Match nested loops | `for ($INIT1; $COND1; $POST1) { for ($INIT2; $COND2; $POST2) { $$$BODY } }` | `for (i=0; i<n; i++) { for (j=0; j<m; j++) { /* ... */ } }` |

### Performance Optimizations

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `unnecessary_copy` | Match unnecessary copies | `memcpy($DEST, $SRC, sizeof($TYPE))` | `memcpy(&dest, &src, sizeof(int));` |
| `inefficient_string_concat` | Match inefficient string concatenation | `strcat($DEST, $SRC)` | `strcat(message, " world");` |
| `malloc_without_check` | Match unchecked mallocs | `$PTR = malloc($SIZE)` | `data = malloc(size);` |
| `repeated_array_element_access` | Match repeated array access | `for ($I = 0; $I < $N; $I++) { $$$_; $ARRAY[$I]; $$$_ }` | `for (i=0; i<n; i++) { sum += array[i]; }` |
| `redundant_condition` | Match redundant conditions | `if ($EXPR) { return 1; } else { return 0; }` | `if (is_valid) { return 1; } else { return 0; }` |

### Security Vulnerabilities

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `buffer_overflow` | Match potential buffer overflows | `strcpy($DEST, $SRC)` | `strcpy(buffer, input);` |
| `format_string_vulnerability` | Match format string vulnerabilities | `printf($USER_INPUT)` | `printf(message);` |
| `gets_call` | Match gets calls | `gets($BUFFER)` | `gets(input);` |
| `integer_overflow` | Match potential integer overflows | `$SMALL_TYPE $VAR = $LARGE_TYPE_EXPR` | `short result = big_num * factor;` |
| `null_pointer_deref` | Match potential null pointer dereferences | `*$PTR` | `*data = 42;` |
| `use_after_free` | Match use after free | `free($PTR); $$$_; *$PTR` | `free(data); /* ... */ value = *data;` |

### Refactoring Patterns

| Pattern Name | Description | Pattern Example | Code Example |
|--------------|-------------|-----------------|--------------|
| `if_return_pattern` | Match early returns | `if ($COND) { return $TRUE_VAL; } return $FALSE_VAL;` | `if (error) { return NULL; } return result;` |
| `void_parameter` | Match void parameters | `$RET_TYPE $NAME(void)` | `int get_count(void)` |
| `switch_without_default` | Match switches without default | `switch ($EXPR) { $$$CASES }` | `switch (status) { case SUCCESS: /*...*/ case ERROR: /*...*/ }` |
| `redundant_null_check` | Match redundant NULL checks | `if ($PTR != NULL) { $$$BODY }` | `if (user != NULL) { process_user(user); }` |
| `loop_counter_size` | Match inefficient loop counters | `for (int $I = 0; $I < $SIZE; $I++)` | `for (int i = 0; i < array_size; i++)` | 