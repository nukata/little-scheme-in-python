;; N-Queens solver in Scheme
(define nqueens
  (lambda (n)
    (define loop
      (lambda (lst result)
        (if (null? lst)
            result
          ((lambda (candidate)
             (set! lst (cdr lst))
             (if (safe-positions? candidate)
                 (if (= (_length candidate) n)
                     (set! result (cons candidate result))
                   (set! lst (_append (cons-range n candidate) lst))))
             (loop lst result))
           (car lst)))))
    (loop (cons-range n '()) '())))

(define _length
  (lambda (lst)
    (if (null? lst)
        0
      (+ 1 (_length (cdr lst))))))

(define _append
  (lambda (lst1 lst2)
    (if (null? lst1)
        lst2
      (cons (car lst1) (_append (cdr lst1) lst2)))))

(define safe-positions? ; (safe-positions? (3 4 1)) => #f i.e. conflicted
  (lambda (lst)
    (if (null? (cdr lst))
        #t
      ((lambda (loop)
         (set! loop
               (lambda (me high low rest)
                 (if (null? rest)
                     #t
                   ((lambda (target)
                      (if (= target me)
                          #f
                        (if (= target high)
                            #f
                          (if (= target low)
                              #f
                            (loop me (+ high 1) (- low 1) (cdr rest))))))
                    (car rest)))))
         ((lambda (me)
            (loop me (+ me 1) (- me 1) (cdr lst)))
          (car lst)))
       '()))))

(define cons-range     ; (cons-range 3 x) => ((3 . x) (2 . x) (1 . x))
  (lambda (n lst)
    (if (= n 0)
        '()
      (cons (cons n lst) (cons-range (- n 1) lst)))))

(display (nqueens 6))
(newline)
;; => ((5 3 1 6 4 2) (4 1 5 2 6 3) (3 6 2 5 1 4) (2 4 6 1 3 5)
