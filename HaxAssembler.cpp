#include <iostream>
#include <string>
#include <fstream>
#include <map>
#include <bitset>
#include <cctype>
#include <cstring>
// Assembler for the Hack assembly language
/*

Staged development:

* Individually code and test each module of the 3 described below

1. Develop a basic assembler that translates assembly programs without symbols
2. Develop an ability to handle symbols
3. Morph the basic assembler to one that can translate any assembly program

Architecture:
Parser: unpacks each instruction into its underlying fields
Code: translates each field into its corresponding bianry value
SymbolTable: manages the symbol table
HAXxembler: initializes the I/O fields and drives the process
*/

class Parser {
public:
    std::string comp(std::string line)
    {   
        std::size_t i_start = line.find('=');
        std::size_t i_end = line.find(';');

        if (i_start == std::string::npos) i_start = 0;
        else i_start++;
        
        if (i_end == std::string::npos) i_end = line.size();
        else if (i_end - i_start == 1) i_end=1;
        else i_end -= i_start;

        return line.substr(i_start, i_end);
    }
    std::string dest(std::string line)
    {
        std::size_t i = line.find('=');
        if (i == std::string::npos) return "";
        return line.substr(0, i);
    }
    std::string jump(std::string line)
    {
        
        std::size_t i = line.find(';');
        if (i == std::string::npos) return "";
        return line.substr(i+1, line.size());
    }
};

class Code {
public:
    std::string comp(std::string s)
    {
        static std::map<std::string, std::string> cc; // comp codes
        cc["0"] = "0101010";
        cc["1"] = "0111111";
        cc["-1"] = "0111010";
        cc["D"] = "0001100";
        cc["A"] = "0110000"; cc["M"] = "1110000";
        cc["!D"] = "0001101";
        cc["!A"] = "0110001"; cc["!M"] = "1110001";
        cc["-D"] = "0001111";
        cc["-A"] = "0110011"; cc["-M"] = "1110011";
        cc["D+1"] = "0011111";
        cc["A+1"] = "0110111"; cc["M+1"] = "1110111";
        cc["D-1"] = "0001110";
        cc["A-1"] = "0110010"; cc["M-1"] = "1110010";
        cc["D+A"] = "0000010"; cc["D+M"] = "1000010";
        cc["D-A"] = "0010011"; cc["D-M"] = "1010011";
        cc["A-D"] = "0000111"; cc["M-D"] = "1000111";
        cc["D&A"] = "0000000"; cc["D&M"] = "1000000";
        cc["D|A"] = "0010101"; cc["D|M"] = "1010101";

        return cc[s];
    }
    std::string dest(std::string s)
    {
        static std::map<std::string, std::string> dc; // destination codes
        dc[""] = "000"; dc["M"] = "001"; dc["D"] = "010";
        dc["MD"] = "011"; dc["A"] = "100"; dc["AM"] = "101";
        dc["AD"] = "110"; dc["AMD"] = "111";
        
        return dc[s];
    }
    std::string jump(std::string s)
    {
        static std::map<std::string, std::string> jc; // jump codes
        jc[""] = "000"; jc["JGT"] = "001"; jc["JEQ"] = "010";
        jc["JGE"] = "011"; jc["JLT"] = "100"; jc["JNE"] = "101";
        jc["JLE"] = "110"; jc["JMP"] = "111";
        
        return jc[s];
    }
};

class HackAssembler {
public:
    void first_pass(std::ifstream& ifs, std::map<std::string, std::string>& st)
    {
        int n = 0;
        std::string line;

        for (int i = 0; ifs.good();i++)
        {
            std::getline(ifs, line);
            if (line != "" && line[0] != '/' && line[0] != '(')
                {n++; continue;}
            else if (line != "" && line[0] == '(') {

                int k = line.find(')');
                st[line.substr(1,k-1)] = std::to_string(n);
                // std::cout << "label: " << line.substr(1,k-1) << std::endl;
                // std::cout << "line: " << n << std::endl;
            }
        }
    }

    void assemble(std::ifstream& ist, std::fstream& fs, std::map<std::string, std::string>& st)
    {
        std::string line;
        int nextAddressToAllocate = 16;
        for (int i = 0; ist.good();i++)
        {
            
            std::getline(ist, line);
            // skip empty lines/comments
            if (line == "" || line[0] == '/' || line[0] == '(') continue;

            std::string instruction;

            // remove whistespace
            for (char ch : line)
                if (!isspace(ch))
                    instruction.push_back(ch);
            
            // remove comment
            std::size_t commentIndex = instruction.find('/');
            if (commentIndex != std::string::npos)
                instruction = instruction.substr(0, commentIndex);
            
            
            if (instruction[0] != '@')
            {
                std::string c = parser.comp(instruction);
                std::string d = parser.dest(instruction);
                std::string j = parser.jump(instruction);

                std::string cc = code.comp(c);
                std::string dd = code.dest(d);
                std::string jj = code.jump(j);

                std::string out = "111" + cc + dd + jj;
                // go to a new line if its not the first command being translated
                
                fs << out << std::endl;
            }
            else
            {
                if (isdigit(instruction[1])) {
                    int x = std::stoi(instruction.substr(1, instruction.size()));
                    instruction = "0" + std::bitset<15>(x).to_string();
                }
                else {
                    instruction = instruction.substr(1, instruction.size());
                    // std::cout << "thing: " << instruction << std::endl;
                    if (st.count(instruction) == 0) {
                        st[instruction] = std::to_string(nextAddressToAllocate);
                        // std::cout << "new instruction to symt: " << instruction << std::endl;
                        // std::cout << "its address: " << nextAddressToAllocate << std::endl;
                        nextAddressToAllocate++;
                        // std::cout << "next address thats available: " << nextAddressToAllocate << std::endl;
                    }
                    int y = std::stoi(st[instruction]);
                    instruction = "0" + std::bitset<15>(y).to_string();
                }
                fs << instruction << std::endl;
            }
        }
    }
private:
    Parser parser;
    Code code;
};

int main(int argc, char* argv[])
{   
    if (argc < 2) {
        std::cerr << "not enough arguments\n";
        return 1;
    }

    // initialize Symbol Table
    std::map<std::string, std::string> symTbl;

    for (int i = 0; i < 16; i++)
        symTbl["R" + std::to_string(i)] = std::to_string(i);

    symTbl["SCREEN"] = "16384"; symTbl["KBD"] = "24576";
    symTbl["SP"] = "0"; symTbl["LCL"] = "1"; symTbl["ARG"] = "2";
    symTbl["THIS"] = "3"; symTbl["THAT"] = "4";

    // perform first pass
    std::ifstream fp{argv[1], std::ifstream::in};
    if (!fp) std::cerr << "can't open input file for first pass: " << argv[1];
    
    HackAssembler a;
    a.first_pass(fp, symTbl);

    std::ifstream ist{argv[1], std::ifstream::in};
    if (!ist) std::cerr << "can't open input file " << argv[1];

    std::string s = argv[1];
    int i = s.find('.');
    s = s.substr(0, i) + ".hack";

    std::fstream fs;
    fs.open(s, std::ios_base::out);
    if (!fs) std::cerr << "failed to open file output stream\n";

     a.assemble(ist, fs, symTbl);
}