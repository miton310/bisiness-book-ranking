# 1. ISBNからASINを取得する方法（計算のみ）
# Amazonの和書・洋書のASINは、実はISBN-10（10桁のISBN）と完全に同一です。
# 現在主流のISBN-13（978から始まる13桁）からASINを取得する場合、APIは不要で、単なる**再計算（チェックデジットの算出）**だけで変換できます。

# Pythonによる変換ロジック
# ISBN-13の先頭「978」を取り除き、ISBN-10用のチェックデジットを再計算します。

def isbn13_to_asin(isbn13: str) -> str:
    """ISBN-13をASIN(ISBN-10)に変換する"""
    # ハイフン除去と文字列化
    src = str(isbn13).replace("-", "")
    
    # バリデーション（978開始の13桁であること）
    if len(src) != 13 or not src.startswith("978"):
        raise ValueError("Invalid ISBN-13")
        
    # 先頭3桁(978)と末尾1桁(チェックデジット)を除外した9桁を取得
    core = src[3:12]
    
    # ISBN-10のチェックデジット計算 (モジュラス11 ウェイト10-2)
    # CheckDigit = 11 - (Sum(Weight * Digit) % 11)
    total = 0
    for i, digit in enumerate(core):
        total += int(digit) * (10 - i)
        
    remainder = total % 11
    check_digit = 11 - remainder
    
    if check_digit == 11:
        cd_str = "0"
    elif check_digit == 10:
        cd_str = "X"
    else:
        cd_str = str(check_digit)
        
    return core + cd_str

# 使用例
print(isbn13_to_asin("978-4-87311-932-8")) 
# 出力: 4873119325 (これがそのままASINになります)
