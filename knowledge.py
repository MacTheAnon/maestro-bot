# knowledge.py
COURSE_NOTES = """
Question / Cue Column	Notes Column: Detailed Content & Examples
What is Python?	• High-Level Language: Designed to be human-readable, abstracting away complex computer memory management.


• Sequential Interpretation: The Python Interpreter reads your script like a recipe, starting at Line 1. If Line 10 depends on a variable created on Line 12, the program will crash with a NameError.
Part 1: print() & Execution	• Standard Output: print() sends data to the console (the human interface).


• Multiple Arguments: Commas in print() act as "auto-formatters." They convert items to strings and inject a single space. 


• Ex: print("Score:", 5) becomes "Score: 5".
Part 2: Data Types (Numeric)	• int (Integer): Whole numbers. Memory-efficient for counting.


• float (Floating Point): Represents real numbers with decimals. 


• Type Promotion: If you multiply an int by a float (e.g., 5 * 1.0), Python "promotes" the result to a float (5.0) to preserve decimal precision.
Part 3: Variables & Names	• Assignment (=): Not a math equation; it’s an action. "Take the thing on the right and shove it into the name on the left."


• Naming Syntax: Must use snake_case (lowercase with underscores) for readability. Invalid: My Variable (spaces), 2nd_place (starts with number), class (reserved keyword).
Part 4: Type Mismatches	• Concatenation (+): This operator is "overloaded." It does math for numbers but "glues" for strings. 


• The Crash: If you try "Age: " + 25, Python doesn't know whether to try and turn "Age" into a number or 25 into text, so it stops (TypeError).
Three Division Operators	• True Division (/): Always returns a float. 10 / 2 is 5.0.


• Floor Division (//): Chops off the decimal. 11 // 3 is 3. Used for "Whole Groups."


• Modulo (%): The "Clock Operator." It gives the remainder. 11 % 3 is 2.
Packing & Parity Logic	• Packing Pattern: items // box_size = filled boxes; items % box_size = leftovers.


• Parity (Even/Odd): num % 2 == 0 is Even. num % 2 != 0 is Odd.


• Circular Logic: (current_index + 1) % total_slots moves a player to the next seat, but resets back to 0 when they reach the end.
Traceback Anatomy	• The "Sandwich" Structure: The top is the "Header," the middle is the "Trace" (where it happened), and the bottom is the "Diagnosis" (the Error Type).


• Reading Strategy: Start at the bottom. If it says ValueError, check the data you are trying to convert.
Syntax vs. Runtime Errors	• SyntaxError: A "Grammar" mistake. The code never even starts running. (e.g., if x = 5: missing a second =).


• Runtime (Type/Value): The "Logic" is okay, but the data is bad. The code starts but "trips" on a specific line.
Comparison & Logic	• Boolean Logic: Evaluates to True or False.


• Short-Circuiting: In an and statement, if the first part is False, Python skips the rest. In an or statement, if the first part is True, it skips the rest.
Loops: Iteration Logic	• While Loops: Great for "Events" (e.g., while user_input != "quit":). Danger: Infinite loops occur if the condition never becomes False.


• For Loops: Great for "Collections" (e.g., for item in grocery_list:).


• range(start, stop, step): Note that stop is exclusive. range(1, 5) gives 1, 2, 3, 4.
Control Flow: Break/Continue	• break: "Eject Button." Exits the loop entirely.


• continue: "Skip Button." Jumps back to the top of the loop for the next turn.
Functions & DRY	• DRY (Don't Repeat Yourself): If you write the same 3 lines of code twice, make it a function.


• The Colon and Indent: Mandatory. The indented block is the "Scope" of the function.
Parameters vs. Arguments	• Parameters: The variables defined in the function signature. The "slots."


• Arguments: The actual data you pass into those slots during a call. The "mail."
The Return "Output Gate"	• print vs return: print is like a billboard (you can see it, but can't use it); return is like a receipt (you get it back and can put it in a variable for later).


• Early Return: Once return is hit, the function is dead. No code after it runs.
Variable Scope	• Local Scope: Variables created inside a function are "born" when the function is called and "die" when it returns. They are invisible to the rest of the file.


• Global Scope: Variables at the top level. Functions can "see" them, but shouldn't usually change them (to avoid "spaghetti code").
Question / Cue Column	Notes Column
What is Python?	• A high-level, easy-to-read programming language used for web development, AI, and data analysis.


• It executes code sequentially from top to bottom.
What is PY101?	• The introductory course in your AAS in AI Software Engineering program.


• Covers fundamental building blocks: strings, numeric types, variables, and logic.
Part 1: print() & Execution	• print() displays values or text to the console.


• Execution Order: Runs top to bottom in order.


• Strings (text) require quotes; numbers do not.


• Comma usage: print("Text", 5) automatically adds a space between different types.
Part 2: Data Types (Numeric)	• int: Whole numbers (e.g., 5).


• float: Numbers with decimals (e.g., 5.0).


• Mixed math: If any value in a math expression is a float, the result is a float.
Part 3: Variables & Names	• Variable: A named "container" for storing a value using =.


• Naming Rules: Use letters, numbers, and _. Cannot start with a number (e.g., 2snacks = Error).


• Clarity: Use descriptive names like ticket_price to make code readable.
Part 4: Type Mismatches	• The + Rule: You cannot use + to join a string and a number (causes a TypeError).


• Example: "Total: " + str(5) ✅ vs "Total: " + 5 ❌


• Solution: Use a comma in print() to safely combine different data types.
Part 5: Logic Modeling	• Translate word problems into math expressions first (e.g., (Quantity * Price) + Extras).


• Inline Math: Calculations can be performed directly inside a print() call.
Three Division Operators	• / (True Division): Standard division; results in a decimal (e.g., 10 / 3 → 3.33...).


• // (Floor Division): Keeps only the whole number part; "How many whole groups?" (e.g., 10 // 3 → 3).


• % (Modulo): Returns the remainder after division.
Key Vocabulary	• Quotient: The result of whole-number division (a // b).


• Remainder: What is left over after making full groups (a % b).
Packing Story Pattern	• total // size: Number of full containers (e.g., 47 muffins // 6 per box = 7 full boxes).


• total % size: Number of items left over (e.g., 47 muffins % 6 = 5 muffins left).
Rebuilding Numbers	• Original number = (quotient * size) + remainder (e.g., (7 * 6) + 5 = 47).
Parity Check (% 2)	• Even: Remainder is 0 (e.g., 8 % 2 → 0).


• Odd: Remainder is 1 (e.g., 13 % 2 → 1).
Cycling with % n	• Modulo creates a repeating loop from 0 to n-1.


• Example: x % 4 results in 0, 1, 2, or 3. It will never be 4.
Real-World Cycles	• Circular Seating: Use player_number % seat_count.


• Game Turns: Use turn % 2 to toggle between players.


• Schedules: Use day % shift_length to rotate workers.
Three Core Data Types	• str (String): Text values in quotes (e.g., "42", "Kaleb").


• int (Integer): Whole numbers (e.g., 42, -5).


• float: Decimal numbers (e.g., 3.14, 2.0).


• Contrast: "3" * 2 → "33" (string repeat) vs 3 * 2 → 6 (math).
type() Function	• Reports the current category of a value without changing it.


• Example: print(type("42")) outputs <class 'str'>.
str() Conversion	• Turns any value into text to allow gluing into other strings.


• Required for concatenation: "Score: " + str(150).
int() vs float()	• int(x): Converts numeric text into a whole number (e.g., "7" → 7).


• float(x): Converts numeric text into a decimal (e.g., "7" → 7.0).
Strong Typing Rule	• Python will not automatically mix strings and numbers using +. Text + 5 causes a crash; use text + str(5) instead.
Variable Reassignment	• A variable's type is determined by its current assigned value, not its name. score = int(score) updates the type.
Traceback	• Python’s report showing where and why a program crashed. It turns the code into a "glass box" to see the failure.
The "Headline" Rule	• Always read the last line first; it contains the error type and specific reason.
Traceback Anatomy	• Header: Indicates a crash.


• File/Line: Exact location of error.


• Error Line: The specific instruction that failed.


• Arrow (^): Points to the exact character causing the issue.
SyntaxError	• Build-time error: Code cannot start because the "shape" is invalid (missing quotes, brackets, etc.).
TypeError	• Run-time error: Incompatible data types used together (e.g., adding string to int).
ValueError	• Run-time error: Type is correct, but value is invalid (e.g., int("hello")).
Week 3: Logic & Cues	Conditionals & Loops Logic
Conditional Statement	• A line of code that checks if something is true/false. Uses if, elif, else.
Comparison Operator	• Used to compare two values: == (equal), != (not equal), >, <, >=, <=.
Logical Operators	• and: Both sides must be True.


• or: At least one side must be True.


• not: Flips True to False and vice versa.
Loops	• While loop: Runs while a condition is True. Best for unknown repetition counts.


• For loop: Runs for each item in a sequence or a set number of times.
Break vs Continue	• break: Stops the loop immediately.


• continue: Skips the current cycle and starts the next one.
Functions (DRY)	• DRY (Don’t Repeat Yourself): Group steps under a name to reuse code.


• def: Keyword to define a function.


• return: The "output gate" that sends data back to the caller.
Scope	• Global: Variables defined at the top level (accessible everywhere).


• Local: Variables created inside a function (deleted when function ends).
 











SUMMARY: In the first three weeks of PY101, I mastered the essential grammar of Python. I learned that Python is a strongly typed, sequential language where data must be explicitly converted (casting) to interact correctly. I utilized the division family (/, //, %) to model real-world packing and cycling problems. Moving into Week 3, I transitioned from simple scripts to functional programming. By following the DRY principle, I can define reusable logic using def. I established a clear mental model for Scope: understanding that Parameters and Local Variables are private to their functions, while Global Variables persist across the file. Finally, I learned that while print() communicates with humans, the return statement is the critical "output gate" that allows functions to pass data back into the main program for storage and further use.

"""
