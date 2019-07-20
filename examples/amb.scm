;; Amb (ambiguous) using continuations
;; cf. https://stackoverflow.com/questions/49390161

(define current-continuation
  (lambda ()
    (call/cc (lambda (cc)
               ;; `cc` will be the value of `k` in `amb`.
               (cc cc)))))

(define fail-stack '())                 ; list of continuations

(define fail
  (lambda ()
    (if (pair? fail-stack)
        ((lambda (bt-point remaining-stack)
           (set! fail-stack remaining-stack)
           ;; `bt-point` will be the value of `k` in `amb`.
           (bt-point bt-point))
         (car fail-stack)
         (cdr fail-stack))
      (error "no backtracking poins" fail-stack))))

(define amb
  (lambda (choices)
    ((lambda (k)
       (if (null? choices)
           (fail)
         ((lambda (choice remaining-choices)
            (set! choices remaining-choices)
            (set! fail-stack (cons k fail-stack))
            choice)
          (car choices)
          (cdr choices))))
     (current-continuation))))

;;----------------------------------------------------------------------

;; (fold f x '(a b c d)) => (f (f (f (f x a) b) c) d)
(define fold
  (lambda (fun x ys)
    (if (null? ys)
        x
      (fold fun
            (fun x (car ys))
            (cdr ys)))))

;; (_reverse '(a b c d)) => (d c b a)
(define _reverse
  (lambda (xs)
    (fold (lambda (xs y) (cons y xs))
          '()
          xs)))

;; Create a list of the results which `(fun)` returns successively on
;; backtracking over `amb` in `fun`.  cf. Prolog findall/3
(define find-all
  (lambda (fun)
    ((lambda (results)
       (call/cc (lambda (end-loop)
                  (set! fail-stack (cons end-loop fail-stack))
                  ;; loop:
                  ((lambda (r)
                     (set! results (cons r results)))
                   (fun))
                  (fail)))              ; goto loop or goto end-loop
       ;; end-loop:
       (_reverse results))
     '())))

(display (find-all (lambda ()
                     ((lambda (x)
                        (list x (amb '(A B C))))
                      (amb '(1 2 3))))))
(newline)
;; => ((1 A) (1 B) (1 C) (2 A) (2 B) (2 C) (3 A) (3 B) (3 C))
