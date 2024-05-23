submit:
	@echo "Zipping Submission..."
	@touch ee282_assign3.zip
	@tar --exclude='jgproject' --exclude='jg_summary.txt' --exclude="Makefile" --exclude=".git" --exclude=".gitignore"  --exclude="cva6/insns/*.v" --exclude="cva6/insns/*.tcl" --exclude="cva6/insns/*.txt" --exclude="ee282_assign3.zip" -czf ee282_assign3.zip .

generate:
	@echo "Generating Instruction Checks..."
	@cd cva6/insns ; python3 generate.py ; 	cd ../..
	
phony: submit generate