下記 @yuki さんの記事を元に修正を行っています。<br>
https://qiita.com/yuki_2020/items/716fa4e4ada65306f688<br><br>

修正点<br>
・保存先をclient.json内で保持<br>
・ファイル名にタイトルを追加<br>
・最新のみ取得を追加<br><br>

ファイル構成<br>
 ・pixiv_auth.py - TOKEN取得用 - 参考サイトよりそのまま利用<br>
 ・pixiv_follow_id_getter.py - 参考サイトよりそのまま利用<br>
 
 参考サイトから修正<br>
 ・pixiv_downloader.py - フォローしているユーザー(pixiv_follow_id_getter.py - で取得された client.json の ids )の作品を取得する <br>
 　　　　　　　　　　　　※タグによるダウンロード判定等、自分には不要と思われる判定は削除しています。<br>
               
 別途追加<br>
 ・pixiv_illust_new.py - フォローしているユーザーの新着のみ取得する(client.json に取得済みの最終IDを保持)<br>
 　　　　　　　　　　　　※pixiv_downloader.py で一括取得以降に新着のみ取得するために作成　(cron で定期的に実行)<br><br>
 ・pixiv_illust_error_download.py - エラーで取得されなかったイラストを再取得する<br>
                         
以降やりたいこと<br>
  ・PixivPy-Async 使用のほうが性能が良いようなのでPixivPy-Asyncを使って同じ処理を作成<br>
