<pre>
下記 @yuki さんの記事を元に修正を行っています。
https://qiita.com/yuki_2020/items/716fa4e4ada65306f688

修正点
・保存先をclient.json内で保持
・最新のみ取得を追加

ファイル構成
 ・pixiv_auth.py - TOKEN取得用 - 参考サイトよりそおのまま利用
 ・pixiv_follow_id_getter.py - 参考サイトよりそのまま利用
 参考サイトから修正
 ・pixiv_downloader.py - フォローしているユーザー(pixiv_follow_id_getter.py - で取得された client.json の ids )の作品を取得する 
 　　　　　　　　　　　　　　※タグによるダウンロード判定等、自分には不要と思われる判定は削除しています。
 別途追加
 ・pixiv_illust_new.py - フォローしているユーザーの新着のみ取得する(client.json に取得済みの最終IDを保持)
                         ※pixiv_downloader.py で一括取得以降に新着のみ取得するために作成　(cron で定期的に実行)
以降やりたいこと
  ・pixiv_downloader.py 取得済みの ids をダウンロード完了毎に削除
　　--- ダウンロードエラー発生時の復帰時に同じユーザーから取得できるように
  ・PixivPy-Async 使用のほうが性能が良いようなのでPixivPy-Asyncを使って同じ処理を作成
</pre>
  
