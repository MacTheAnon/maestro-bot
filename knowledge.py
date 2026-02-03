# knowledge.py
COURSE_NOTES = """
--- GENERAL INFO ---
MAESTRO PY101 Course notes by Kaleb McIntosh!
What is Python?
• A high-level, easy-to-read programming language used for web development, AI, and data analysis.




• It executes code sequentially from top to bottom.
What is PY101?
• The introductory course in your AAS in AI Software Engineering program.




• Covers fundamental building blocks: strings, numeric types, variables, and logic.
Question / Cue Column
Notes Column
Part 1: print() & Execution
• print() displays values or text to the console.




• Execution Order: print() runs top to bottom with the rest of the code (Python executes in order).




• Strings (text) require quotes; numbers do not.




• Comma usage: print("Text", 5) automatically adds a space between different types.
Part 2: Data Types (Numeric)
• int: Whole numbers (e.g., 5).




• float: Numbers with decimals (e.g., 5.0).




• Mixed math: If any value in a math expression is a float, the result is a float.
Part 3: Variables & Names
• Variable: A named "container" for storing a value using =.




• Naming Rules: Use letters, numbers, and _. Cannot start with a number (e.g., 2snacks = Error).




• Clarity: Use descriptive names like ticket_price to make code readable.
Part 4: Type Mismatches
• The + Rule: You cannot use + to join a string and a number (causes a TypeError).




• Example: "Total: " + str(5) ✅ vs "Total: " + 5 ❌




• Solution: Use a comma in print() to safely combine different data types.
Part 5: Logic Modeling
• Translate word problems into math expressions first (e.g., (Quantity * Price) + Extras).




• Inline Math: Calculations can be performed directly inside a print() call.
Question / Cue Column
Notes Column
Three Division Operators
• / (True Division): Standard division; results in a decimal (e.g., 10 / 3 → 3.33...).




• // (Floor Division): Keeps only the whole number part; "How many whole groups?" (e.g., 10 // 3 → 3).




• % (Modulo): Returns the remainder after division.
Key Vocabulary
• Quotient: The result of whole-number division (a // b).




• Remainder: What is left over after making full groups (a % b).
Packing Story Pattern
• total // size: Number of full containers (e.g., 47 muffins // 6 per box = 7 full boxes).




• total % size: Number of items left over (e.g., 47 muffins % 6 = 5 muffins left).
Rebuilding Numbers
• Original number = (quotient * size) + remainder (e.g., (7 * 6) + 5 = 47).
Question / Cue Column
Notes Column
Parity Check (% 2)
• Even: Remainder is 0 (e.g., 8 % 2 → 0).




• Odd: Remainder is 1 (e.g., 13 % 2 → 1).
Cycling with % n
• Modulo creates a repeating loop from 0 to n-1.




• Example: x % 4 will result in 0, 1, 2, or 3. It will never be 4.
Real-World Cycles
• Circular Seating: Use player_number % seat_count.




• Game Turns: Use turn % 2 to toggle between players.




• Schedules: Use day % shift_length to rotate workers.
Question / Cue Column
Notes Column
Three Core Data Types
• str (String): Text values in quotes (e.g., "42", "Kaleb").




• int (Integer): Whole numbers (e.g., 42, -5).




• float: Decimal numbers (e.g., 3.14, 2.0).




• Contrast: "3" * 2 → "33" (string repeat) vs 3 * 2 → 6 (math).




• Key Concept: Quotes define a string. "42" is text; 42 is a number.
type() Function
• Reports the current category of a value without changing it.




• Example: print(type("42")) outputs <class 'str'>.
str() Conversion
• Turns any value into text to allow gluing into other strings.




• Required for concatenation: "Score: " + str(150).




• print() with commas auto-converts: print("Score:", 150).
int() vs float()
• int(x): Converts numeric text into a whole number (e.g., "7" → 7).




• float(x): Converts numeric text into a decimal (e.g., "7" → 7.0).
Strong Typing Rule
• Python will not automatically mix strings and numbers using +.




• text + 5 causes a crash; use text + str(5) instead.
Decision Workflow
• For Math: Ensure values are int or float.




• For Text: Convert everything to str before using +.
Variable Reassignment
• A variable's type is determined by its current assigned value, not its name.




• Running score = int(score) updates the type from string to integer.
Question / Cue Column
Notes Column
Traceback
• Python’s report showing where and why a program crashed.




• Turns the code into a "glass box" to see the internal failure.
The "Headline" Rule
• Always read the last line first; it contains the error type and specific reason.
Traceback Anatomy
• Header: Indicates a crash occurred.




• File/Line: Pinpoints the exact location of the error.




• Error Line: Shows the specific instruction that failed.




• Arrow (^): Points to the exact character causing the issue.
SyntaxError
• Build-time error: Happens before the code even starts running.




• Cause: The "shape" of the code is invalid (e.g., missing quotes or )).
TypeError
• Run-time error: Occurs while the code is running.




• Cause: Using incompatible data types together (e.g., adding a string to an integer).
ValueError
• Run-time error: The data type is correct, but the specific value is invalid (e.g., int("hello")).
Debugging Steps
1. Read bottom line for the error type.




2. Locate the error line indicated above the message.




3. Apply the fix (e.g., using str() for conversion or fixing parentheses).
Question / Cue Column
Notes Column
1. print() differences?
• print(x, y): Commas add spaces automatically and handle multiple types safely.




• + Concatenation: Requires all parts to be strings; must manually add spaces and use str().
2. Why "4" * 3 = "444"?
• String Repetition: A string multiplied by an int repeats text rather than performing math.
3. Real-life // and %?
• Packing Scenario: 13 // 4 = 3 (Full boxes), 13 % 4 = 1 (Leftover muffin).
4. Type of 19 / 2?
• Type: float (True division always results in a float). Value: 9.5.
5. Safe printing for 7.5?
• print("Total:", total, "dollars") (Commas) or print("Total: " + str(total) + " dollars") (Casting).
6. Example for int()?
• Scenario: Math on text input. age = int("21") + 1.
7. TypeError vs. "7" * 2?
• TypeError is a crash (e.g., "A" + 1); repetition is a valid text operation.
8. When to use round(x, 2)?
• For human-readable currency (though Python displays 7.0 for 7.00).
Types & Casting - Exam Review
Core Conversions:




• str(x): Turns any value into a string. Required for joining text with +.




• int(x): Turns numeric text into a whole number (e.g., "10" → 10).




• float(x): Turns numeric text into a decimal (e.g., "10" → 10.0).





Memorize These Behaviors:




• The "42" Trap: "42" is a string; 42 is an int.




• String * Number: "3" * 2 results in "33" (repetition).




• Int * Number: 3 * 2 results in 6 (math).




• The + Rule: You cannot do "A" + 1. This causes a TypeError.
Question / Cue Column
Notes Column: Detailed Content
Why use functions? (DRY)
• Problem: Copy-pasting code (like a receipt header) leads to errors and maintenance headaches.




• Solution: DRY (Don’t Repeat Yourself).




• Write code once, reuse it many times by grouping steps under a single name.
What is a function?
• A named block of code that performs a specific task.




• You define it once and call it whenever needed.




• It acts like inventing a new command in Python (e.g., print_receipt_header()).
Basic Structure
• def: Keyword telling Python a function is being defined.




• Function Name: Descriptive, uses snake_case, no spaces, and cannot start with a number.




• () (Parentheses): Holds input names (parameters) or stays empty.




• : (Colon): Required at the end of the def line.




• Indented Body: All lines inside must be indented (usually 4 spaces) to show they belong to the function.
Defining vs. Calling
• Defining: Python learns and stores the instructions but does not run them yet.




• Calling: Python jumps to the function, runs the body, then returns to the main script.
Parameters vs. Arguments
• Parameter: The variable name inside the function's parentheses (e.g., customer_name).




• Argument: The actual value passed during a call (e.g., "Kaleb" or a variable like customer1).
Parameter Practice
• 0 Parameters: Performs the same static task every time.




• 1 Parameter: Customizes one piece of data (e.g., a name).




• 2 Parameters: Customizes multiple pieces (e.g., name and store name).
Function Call Flow
• Step 1: Main script reaches the call line.




• Step 2: Python jumps to the function and assigns argument values to parameters.




• Step 3: The indented body runs line by line.




• Step 4: Python returns to the main script where it left off.
Question / Cue Column
Notes Column: Detailed Content
What is a function?
• A reusable block of code that has a name, can take inputs, runs a set of steps, and can hand back a result.
Function Definition Syntax
• Defined with the def keyword followed by the function name, parameters in parentheses, and a colon.




• The indented block under the def line is the body.
Parameters vs. Arguments
• Parameters: Placeholder names in the function definition (e.g., price, tax_amount).




• Arguments: The actual values passed during a call (e.g., add_tax(50, 8)).




• Positional Binding: Python matches arguments to parameters by their order.
The return Keyword
• Acts as the function’s "output gate" that sends a value back to the caller.




• Once hit, Python leaves the function and hands the value back to be stored in a variable.
Execution Flow & Tracing
• Standard Flow: Caller line → Function body (line by line) → return → Back to caller.




• Tracing: Using print() messages before, inside, and after a call to verify execution order and variable values.
Question / Cue Column
Notes Column: Detailed Content
Key Vocabulary
• Function: A reusable block of code that executes when called.




• print(): Displays text for humans; does not hand data back to the program.




• return: The "output gate" that sends a value to the caller and instantly stops the function.




• Return Value: Data handed back by return that can be stored in a variable.




• Bare Return: A return with no value that exits a function early, giving back None.
print() vs. return
• print() = Side effect for humans (console output).




• return = Data output for code (reusable, storable).




• Rule: You see print on the screen; you use return in your logic.
Sending vs. Receiving
• Sender (Inside function): return something.




• Receiver (Outside function): result = my_func(...).




• These must work as a pair to use the value later in your script.
The "Early Return" Rule
• When Python hits a return, it skips all lines below it inside that function.




• This applies to both specific values (e.g., return 5) and bare returns.
Multiple return Lines
• You can have multiple return statements, but only the first one executed runs; all subsequent code is ignored.
Questions / Terms
Notes
Term: Scope
• Defines where a variable's name is valid and usable in a program.




• Focuses on local scope (inside functions) and global scope (top-level file).
Global Scope / Variables
• Defined at the top level of the file, outside all functions.




• Exists for the entire duration the program runs.




• Can be read inside functions unless "shadowed" by a local variable with the same name.
Local Scope / Variables
• Created inside a function body and exists only while the function is running.




• Lifecycle: Created at function entry and destroyed when the function returns.




• Attempting to use a local variable outside its function results in a NameError.
Python's Lookup Rule
• When a name is used inside a function, Python looks in the Local scope first.




• If not found locally, it falls back to the Global scope.
Term: Shadowing
• Occurs when a local variable shares the same name as a global variable, hiding the global one inside the function.




• Changes to the local variable do not affect the global variable.
Term: Parameter
• A variable name in a function definition that receives a value (argument) when called.




• Parameters are local variables that exist only inside the function.
The "Good Habit" Path
• Prefer using parameters to bring data in and return to send data out.




• This makes code more reusable, testable, and predictable compared to overusing globals.

 SUMMARY: In the first two weeks of PY101, I mastered the essential grammar of Python. I learned that Python is a strongly typed, sequential language where data must be explicitly converted (casting) to interact correctly. I utilized the division family (/, //, %) to model real-world packing and cycling problems.
The core of my progress involved moving from simple scripts to functional programming. By following the DRY principle, I can define reusable logic using def. I established a clear mental model for Scope: understanding that Parameters and Local Variables are private to their functions, while Global Variables persist across the file. Finally, I learned that while print() communicates with humans, the return statement is the critical "output gate" that allows functions to pass data back into the main program for storage and further use.
 
 
 
 
 


"""
