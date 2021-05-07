from smickelscript import lexer
from typing import List
from functools import reduce


def require_all_equal(sources: List[str]):
    def compare(head, other):
        assert head == other
        return head

    tokens_lst = map(lexer.tokenize_str, sources)
    tokens_types_lst = map(lambda x: list(map(type, x)), tokens_lst)
    reduce(compare, tokens_types_lst)


def test_empty():
    tokens = lexer.tokenize_str("")
    assert tokens == []


def test_comments():
    src = """
    // This is a comment.
    # This also is a comment.
    """
    tokens = lexer.tokenize_str(src)
    assert len(list(map(type, tokens))) == 2


def test_hello_world():
    src = """
    func main() {
        println("Hello World");
    }
    """
    tokens = lexer.tokenize_str(src)
    assert list(map(type, tokens)) == [
        lexer.KeywordToken,
        lexer.IdentifierToken,
        lexer.ArgumentsOpenToken,
        lexer.ArgumentsCloseToken,
        lexer.ScopeOpenToken,
        lexer.IdentifierToken,
        lexer.ArgumentsOpenToken,
        lexer.StringLiteralToken,
        lexer.ArgumentsCloseToken,
        lexer.SemiToken,
        lexer.ScopeCloseToken,
    ]


def test_even():
    src = """
    func even(n: number): bool {
        if (n == 0) { return true; }
        return odd(n - 1);
    }
    """
    tokens = lexer.tokenize_str(src)
    assert list(map(type, tokens)) == [
        # func even(n: number): bool {
        lexer.KeywordToken,
        lexer.IdentifierToken,
        lexer.ArgumentsOpenToken,
        lexer.IdentifierToken,
        lexer.TypehintToken,
        lexer.TypeToken,
        lexer.ArgumentsCloseToken,
        lexer.TypehintToken,
        lexer.TypeToken,
        lexer.ScopeOpenToken,
        # if (n == 0) { return true; }
        lexer.KeywordToken,
        lexer.ArgumentsOpenToken,
        lexer.IdentifierToken,
        lexer.EqualToken,
        lexer.NumberLiteralToken,
        lexer.ArgumentsCloseToken,
        lexer.ScopeOpenToken,
        lexer.KeywordToken,
        lexer.KeywordToken,
        lexer.SemiToken,
        lexer.ScopeCloseToken,
        # return odd(n-1);
        lexer.KeywordToken,
        lexer.IdentifierToken,
        lexer.ArgumentsOpenToken,
        lexer.IdentifierToken,
        lexer.SubtractionToken,
        lexer.NumberLiteralToken,
        lexer.ArgumentsCloseToken,
        lexer.SemiToken,
        # }
        lexer.ScopeCloseToken,
    ]


def test_sommig():
    src = """
    func sommig(n: number): bool {
        var result = 0;
        while (n >= 1) {
            result = result + n;
            n = n - 1;
        }
        return result;
    }
    """
    tokens = lexer.tokenize_str(src)
    assert list(map(type, tokens)) == [
        # func sommig(n: number): bool {
        lexer.KeywordToken,
        lexer.IdentifierToken,
        lexer.ArgumentsOpenToken,
        lexer.IdentifierToken,
        lexer.TypehintToken,
        lexer.TypeToken,
        lexer.ArgumentsCloseToken,
        lexer.TypehintToken,
        lexer.TypeToken,
        lexer.ScopeOpenToken,
        # var result = 0;
        lexer.KeywordToken,
        lexer.IdentifierToken,
        lexer.AssignmentToken,
        lexer.NumberLiteralToken,
        lexer.SemiToken,
        # while (n >= 1) {
        lexer.KeywordToken,
        lexer.ArgumentsOpenToken,
        lexer.IdentifierToken,
        lexer.GreaterOrEqualToken,
        lexer.NumberLiteralToken,
        lexer.ArgumentsCloseToken,
        lexer.ScopeOpenToken,
        # result = result + n;
        lexer.IdentifierToken,
        lexer.AssignmentToken,
        lexer.IdentifierToken,
        lexer.AdditionToken,
        lexer.IdentifierToken,
        lexer.SemiToken,
        # n = n - 1;
        lexer.IdentifierToken,
        lexer.AssignmentToken,
        lexer.IdentifierToken,
        lexer.SubtractionToken,
        lexer.NumberLiteralToken,
        lexer.SemiToken,
        # }
        lexer.ScopeCloseToken,
        # return result;
        lexer.KeywordToken,
        lexer.IdentifierToken,
        lexer.SemiToken,
        # }
        lexer.ScopeCloseToken,
    ]


def test_odd_different_whitespaces():
    require_all_equal(
        [
            """
            func odd(n:number):bool{
            if(n==0){return false;}
            return even(n- 1);}
            """,
            """
            func
            odd
            (
            n
            :
            number
            )
            :
            bool
            {
            if(
            n
            ==
            0
            )
            {

            return 
               
            false
            ;
            }
            return
            even
            (
            n
            -
            1
            )
            ;
            }
            """,
            "func odd(n:number):bool{if(n==0){return false;}return even(n- 1);}",
            "func odd(n:number):bool{if(n==0){return false;}return even(n - 1);}",
        ]
    )


def test_negative_integers():
    src = "var a = -1;"
    tokens = lexer.tokenize_str(src)
    assert tokens == [
        lexer.KeywordToken(1, "var"),
        lexer.IdentifierToken(1, "a"),
        lexer.AssignmentToken(1),
        lexer.NumberLiteralToken(1, "-1"),
        lexer.SemiToken(1),
    ]


def test_negative_integers_no_semi():
    src = "var a = -1"
    tokens = lexer.tokenize_str(src)
    assert tokens == [
        lexer.KeywordToken(1, "var"),
        lexer.IdentifierToken(1, "a"),
        lexer.AssignmentToken(1),
        lexer.NumberLiteralToken(1, "-1"),
    ]


def test_negative_integers_spacing():
    require_all_equal(["n = n- 1;", "n=n- 1;", "n = n- 1;"])
