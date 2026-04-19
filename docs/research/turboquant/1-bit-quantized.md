# QJL: 1-Bit Quantized JL Transform for KV Cache Quantization with Zero Overhead

Amir Zandieh Independent Researcher `amir.zed512@gmail.com`

Majid Daliri Insu Han[∗] New York University Adobe Research `daliri.majid@nyu.edu insuh@adobe.com`

July 19, 2024

## **Abstract**

Serving LLMs requires substantial memory due to the storage requirements of Key-Value (KV) embeddings in the KV cache, which grows with sequence length. An effective approach to compress KV cache is quantization. However, traditional quantization methods face significant memory overhead due to the need to store quantization constants (at least a zero point and a scale) in full precision per data block. Depending on the block size, this overhead can add 1 or 2 bits per quantized number. We introduce QJL, a new quantization approach that consists of a Johnson-Lindenstrauss (JL) transform followed by sign-bit quantization. In contrast to existing methods, QJL eliminates memory overheads by removing the need for storing quantization constants. We propose an asymmetric estimator for the inner product of two vectors and demonstrate that applying QJL to one vector and a standard JL transform without quantization to the other provides an unbiased estimator with minimal distortion. We have developed an efficient implementation of the QJL sketch and its corresponding inner product estimator, incorporating a lightweight CUDA kernel for optimized computation. When applied across various LLMs and NLP tasks to quantize the KV cache to only 3 bits, QJL demonstrates a more than fivefold reduction in KV cache memory usage without compromising accuracy, all while achieving faster runtime. Codes are available at `https://github.com/amirzandieh/QJL` .

## **1 Introduction**

Large language models (LLMs) have garnered significant attention and demonstrated remarkable success in recent years. Their applications span various domains, including chatbot systems [1, 3] to text-to-image [28, 11, 24], text-to-video synthesis [26], coding assistant [7] and even multimodal domain across text, audio, image, and video [25]. The Transformer architecture with self-attention mechanism [32] is at the heart of these LLMs as it enables capturing intrinsic pairwise correlations across tokens in the input sequence. The ability of LLMs grows along with their model size [17], which leads to computational challenges in terms of huge memory consumption.

Deploying auto-regressive transformers during the generation phase is costly because commercial AI models must simultaneously serve millions of end users while meeting strict latency requirements. One significant challenge is the substantial memory needed to store all previously generated keyvalue (KV) embeddings in cache to avoid recomputations. This has become a major memory and speed bottleneck, especially for long context lengths. Additionally, the GPU must load the entire

> ∗Work done while at Yale University.

**==> picture [469 x 293] intentionally omitted <==**

**----- Start of picture text -----**<br>
Prompt Encoding Decoding (Token Generation)<br>(ATTN-MLP-LAYERNORM)x 𝐿 (ATTN-MLP-LAYERNORM)x 𝐿 Attention  cache<br>LLM encoding vector LLM<br>q<br>Prompt  Answer<br>what is 20+24? K V 44 softmax ( q [⊤] K [⊤] ) V<br>cache<br>Key Embed. k  ∈ R [d] S  ·  k  ∈ R [m] sign ( Sk )  ∈{± 1 } [m] KV Cache Quantization<br>· ∥ k ∥ 2  /m<br>sign ( )<br>JL S ∈ R [m][×][d] QJL ( S ,  k ) K V<br>transform S ij ∼N (0 ,  1) Quantization QJL Per-token  ( · ) QuantizationPer-token<br>Lemma 3.2 & 3.5<br>⟨ Sq ,  QJL ( S ,  k ) ⟩≈ε ⟨ q ,  k ⟩<br>Query Embed. q ∈ R [d] S  ·  q ∈ R [m] Cache<br>×<br>**----- End of picture text -----**<br>

Figure 1: Overview of the KV cache quantization via Quantized JL (QJL) transform

KV cache from its main memory to shared memory for each token generated, resulting in low arithmetic intensity and leaving most GPU threads idle. Therefore, reducing the KV cache size while maintaining accuracy is crucial.

There are several approaches to address this challenge. One method involves reducing the number of heads in the KV cache using multi-query attention [29] and multi-group attention [2], but these require fine-tuning the pre-trained models or training from scratch. Another line of work tries to reduce the KV cache size by pruning or evicting unimportant tokens [39, 21, 33, 37]. Additionally, some recent works tackle the issue from a system perspective, such as offloading [30] or using virtual memory and paging techniques in the attention mechanism [18].

A simple yet effective approach is to quantize the floating-point numbers (FPN) in the KV cache using fewer bits. Several quantization methods have been proposed specifically for the KV cache [36, 34, 10, 16, 38]. Most recently, KIVI [22] and KVQuant [13] proposed per-channel quantization for the key cache to achieve better performance. However, all existing quantization methods for the KV cache face significant “memory overhead” issues. Specifically, all these methods group the data into blocks, either channel-wise or token-wise, and calculate and store quantization constants (at least a zero point and a scale) for each group. Depending on the group size, this overhead can add approximately 1 or 2 additional bits per quantized number, which results in significant computational overhead. In this work, our goal is to develop an efficient, data-oblivious quantization method, referred to as a _sketching technique_ . This method, which we call QJL, does not need to be tuned by or adapted to the input data with significantly less overhead than prior works, without any loss in performance.

## **1.1 Overview of Contributions**

The decoding phase in the attention mechanism involves the following computations: (1) computing attention scores by applying the softmax function to the inner product between the current query embedding and all previously generated keys, and (2) multiplying the attention scores with all previously generated values. To make the attention score calculations in step (1) more memory efficient, we quantize the keys in the cache. We introduce a quantization scheme for key embeddings, named QJL, leveraging randomized sketching techniques. Alongside, we develop a high-accuracy estimator for the inner product of query/key pairs, crucial for mitigating errors amplified by the softmax operation in attention score calculations.

Firstly, we revisit a fundamental concept in numerical linear algebra: applying a JohnsonLindenstrauss (JL) transform, i.e., a random Gaussian projection, to a pair of vectors and then computing the inner product of the projected vectors provides an unbiased and low-distortion estimator for their original inner product [8]. To address the key cache quantization problem, our aim is to quantize the result after applying the JL transform to a key embedding, ideally to just a single bit. Surprisingly, we prove that by applying the JL transform to a key embedding and then quantizing the result to a single bit (the sign bit), while applying the same JL transform to the query embedding without quantization, we still obtain an unbiased estimator of their inner product (see Lemma 3.2). Moreover, the distortion of this estimator is small and comparable to that of the standard JL transform (see Lemma 3.5). In Theorem 3.6, we demonstrate that the proposed inner product estimator based on QJL achieves a relative distortion of 1 _± ε_ on the final attention scores. Notably, the number of required bits for representing quantized keys is independent of the embedding dimension and scales logarithmically with the context length, using a fixed number of bits per token.

Thus the QJL sketch combines a JL transform—a random Gaussian projection—with quantization to the sign bit. An overview of this approach is illustrated in Figure 1. Unlike previous methods, the QJL sketch can quantize vectors with zero overhead because it does not require grouping the data and storing quantization constants (zeros and scales) per group. Furthermore, this is a data-oblivious algorithm that does not rely on specific input, requires no tuning, and can be easily parallelized and applied in real-time.

The value cache quantization used to make step (2) memory efficient is known to be a straightforward task, and a standard token-wise quantization is very effective and efficient in practice, as observed in prior work [22, 13]. Hence, we follow the same approach for the value therein.

Furthermore, we analyzed the distribution of outliers in large language models (LLMs). We observed that while there are no significant outliers in the initial layers, certain fixed key embedding channels (coordinates) in the deeper layers exhibit considerably larger magnitudes (see Figure 2). To address this, we identify these outlier channels during the prompt phase and simply apply two independent copies of our quantizer to the outliers and inliers separately.

The QJL transform and its accompanying inner product estimator are highly efficient and GPU-friendly algorithms. In particular, we provide a lightweight CUDA kernel for their efficient computation. We apply QJL and our inner product estimator to compress the KV cache in several LLMs, including Llama-2 [31] and its fine-tuned models by long sequence [19], under various NLP tasks. Our results show that quantizing the KV cache to only 3 bits per FPN results in no accuracy drop compared to the exact model with 16 bits per FPN while reducing cache memory usage by over fivefold and increasing the generation speed significantly for long contexts. For example, our proposed quantization shows better F1 scores on long-range question-answering tasks from LongBench [4] (a collection of long-context datasets) compared to the recent KV cache quantization methods, while minimizing memory overheads.

## **2 Preliminaries: Token Generation in Attention**

Deploying auto-regressive language models for inference involves performing attention decoding in an online setting, where key and value embeddings from each transformer layer are cached in memory to remove redundant computations. The model sequentially uses and updates the KV cache to generate the next token, one at a time.

More precisely, in every phase of token generation, the stream of tokens is represented by a triplet of vectors called by the query, key, and value embeddings, respectively. Let _**q** i,_ _**k** i,_ _**v** i ∈_ R _[d]_ be the triplet at _i_ -th generation phase and _n_ be the total number of tokens in the stream so far either in the prompt encoding (prefill) or the generation (decoding) phase. Then, the attention output in _n_ -th generation phase can be written as

**==> picture [291 x 28] intentionally omitted <==**

where `Score` _∈_ R _[n]_ is the vector of attention scores defined as:

**==> picture [357 x 12] intentionally omitted <==**

The output embedding _**o** n_ will be used for computing the next tokens in the stream _**q** n_ +1 _,_ _**k** n_ +1 _,_ _**v** n_ +1 unless the generation phase terminates. Observe that to compute output _**o** n_ , one needs to store all previous key and value embeddings _{_ _**k** i,_ _**v** i}i∈_ [ _n_ ] and keeping them in full precision requires significant memory for long-context inputs. The time complexity to compete Equation (2) is _O_ ( _nd_ ) due to the computation of _n_ inner products. Additionally, the inference speed is also impacted by the KV cache size, as the KV cache must be loaded from GPU main memory for every token generated, resulting in low arithmetic intensity and underutilization of GPU cores [27]. In this work, we focus on compressing the KV cache by quantizing tokens, thereby reducing the memory required to store each key or value embedding in the cache.

## **3 Quantized Johnson-Lindenstrauss (QJL) Transform**

Our goal is to save memory space for storing the KV cache while the inner product between query and key remains undistorted. To achieve this, we first transform the embedding vectors using a random projection that preserves the inner products, acting as a preconditioning step, and then quantize the result. Specifically, we project the input vectors onto a random subspace by applying the Johnson-Lindenstrauss (JL) transform [15], which amounts to multiplying by a random Gaussian matrix. The inner product of the resulting vectors after applying this projection provides an unbiased and low-distortion estimator for the inner product of the original vectors [8]. We introduce a 1-bit Johnson-Lindenstrauss transform, comprising a JL transformation followed by quantization to a single sign bit, and demonstrate its ability to offer an unbiased and low-distortion inner product estimator. We complement our binary quantizer by developing an unbiased estimator for the inner product of the quantized vector with any arbitrary vector. This inner product estimator is asymmetric, as one of the vectors is quantized to a single bit while the other remains unquantized, making it well-suited for the KV cache mechanism. The Quantized Johnson-Lindenstrauss (QJL) transformation, acting as a 1-bit quantizer, alongside our proposed estimator, is formally defined in the following definition:

**Definition 3.1** (QJL and inner product estimator) **.** For any positive integers _d, m_ , let _**S** ∈_ R _[m][×][d]_ be a JL transform matrix, i.e., entries of _**S**_ are i.i.d. samples from the zero mean and unit variance

Normal distribution. The QJL is a mapping function _HS_ : R _[d] →{−_ 1 _,_ +1 _}[m]_ defined as:

**==> picture [326 x 14] intentionally omitted <==**

Furthermore, for any pair of vectors _**k** ,_ _**q** ∈_ R _[d]_ the estimator for their inner product _⟨_ _**q** ,_ _**k** ⟩_ based on the aforementioned quantizer is defined as:

**==> picture [342 x 26] intentionally omitted <==**

Now, we show that the inner product estimator `ProdQJL` ( _**q** ,_ _**k**_ ), exactly like the inner product of JL-transformed vectors without quantization to sign bit, is an unbiased estimator. The crucial point to note is that if we applied QJL to both vectors _**q**_ and _**k**_ in Equation (4), we would obtain an unbiased estimator for the angle between these vectors, as shown in [6]. However, to estimate the inner product one needs to apply the cosine function on top of the angle estimator, which results in a biased estimation. Thus, to achieve an unbiased inner product estimator, it is necessary to asymmetrically apply quantization to the JL transform of only one of the vectors _**q**_ and _**k**_ .

**Lemma 3.2** (Inner product estimator `ProdQJL` is unbiased) **.** _For any vectors_ _**q** ,_ _**k** ∈_ R _[d] the expected value of the estimator_ `ProdQJL` ( _**q** ,_ _**k**_ ) _defined in Equation_ (4) _is:_

**==> picture [120 x 18] intentionally omitted <==**

_where the expectation is over the randomness of the JL matrix_ _**S** in Definition 3.1._

_Proof._ Let _**s**_ 1 _,_ _**s**_ 2 _, . . ._ _**s** m_ denote the rows of the JL matrix _**S**_ . Additionally, let us decompose _**q**_ to its projection onto the vector _**k**_ and its orthogonal component, i.e., _**q**[⊥][k]_ := _**q** −[⟨] ∥_ _**[q] k**[,] ∥_ _**[k]**_[2] 2 _[⟩][·]_ _**[ k]**_[.][We][can][write,]

**==> picture [382 x 111] intentionally omitted <==**

Since _**s** i_ ’s have identical distributions, we have:

**==> picture [378 x 27] intentionally omitted <==**

To calculate the above expectation let us define variables _x_ := _**s**[⊤]_ 1 _**[k]**_[and] _[y]_[:=] _**[ s]**[⊤]_ 1 _**[q]**[⊥][k]_[.][Note][that] _[x]_ and _y_ are both zero-mean Gaussian random variables and because _⟨_ _**q**[⊥][k] ,_ _**k** ⟩_ = 0. By the following Fact 3.3, _x_ and _y_ are independent.

_Fact_ 3.3 _._ If _**x** ∈_ R _[d]_ is a vector of i.i.d. zero-mean normal entries with variance _σ_[2] and _A ∈_ R _[m][×][d]_ is a matrix, then _**A** ·_ _**x**_ is a normal random variable with mean zero and covariance matrix _σ_[2] _·_ _**AA**[⊤]_ .

This implies that the second expectation term above is zero because E � _**s**[⊤]_ 1 _**[q]**[⊥][k][ ·]_ `[ sign]`[(] _**[s]**[⊤]_ 1 _**[k]**_[)] � = E[ _y ·_ `sign` ( _x_ )] = E[ _y_ ] _·_ E[ `sign` ( _x_ )] = 0. Furthermore, _x_ is a Gaussian random variable with mean zero and variance _∥_ _**k** ∥_[2] 2[.][Therefore,][we][have]

**==> picture [236 x 27] intentionally omitted <==**

where the equality comes from the following Fact 3.4:

_Fact_ 3.4 (Moments of Normal Random Variable) _._ If _x_ is a normal random variable with zero mean and variance _σ_[2] , then for any integer _ℓ_ , the _ℓ_ -th moment of _x_ is E � _|x|[ℓ]_[�] = _σ[ℓ] ·_ 2 _[ℓ/]_[2] Γ(( _ℓ_ + 1) _/_ 2) _/[√] π_ . This completes the proof of Lemma 3.2.

Now we show that the inner product estimator `ProdQJL` in Definition 3.1, just like the estimators based on the standard JL transform, has a bounded distortion with high probability.

**Lemma 3.5** (Distortion of inner product estimator `ProdQJL` ) **.** _For any vectors_ _**q** ,_ _**k** ∈_ R _[d] if the estimator_ `ProdQJL` ( _**q** ,_ _**k**_ ) _is defined as in Equation_ (4) _for QJL with dimension m ≥_[4] 3 _[·]_[1+] _ε_[2] _[ε]_[log][2] _δ[,][then:]_

**==> picture [216 x 17] intentionally omitted <==**

_where the probability is over the randomness of the JL matrix_ _**S** in Definition 3.1._

_Proof._ First note that, letting _**s**_ 1 _,_ _**s**_ 2 _, . . ._ _**s** m_ denote the rows of the JL transform matrix _S_ , we have:

**==> picture [262 x 32] intentionally omitted <==**

Since _**s** i_ ’s are i.i.d. the above is indeed the average of _m_ i.i.d. estimators defined as _zi_ := ~~�~~ _π/_ 2 _· ∥_ _**k** ∥_ 2 _·_ _**s**[⊤] i_ _**[q]**[ ·]_ `[ sign]`[(] _**[s]**[⊤] i_ _**[k]**_[)][for] _[ i][ ∈]_[[] _[m]_[]][.][Let][us now calculate][the] _[ℓ]_[-th moment][of] _[ z][i]_[using][ Fact][3.4][:]

**==> picture [413 x 27] intentionally omitted <==**

where the second equality above follows because _**s**[⊤] i_ _**[q]**_[is][a][Gaussian][random][variable][with][mean][zero] and variance _∥_ _**q** ∥_[2] 2[along][with][Fact][3.4][.][Now][we][can][prove][the][result][by][invoking][the][unbiasedness][of] the estimator, Lemma 3.2, along with an appropriate version of Bernstein inequality and using the moment bounds in Equation (5). More specifically, our moment calculation in Equation (5) implies:

**==> picture [419 x 29] intentionally omitted <==**

Therefore, by invoking a proper version of the Bernstein inequality, for instance Corollary 2.11 from [5], we have the following:

**==> picture [340 x 28] intentionally omitted <==**

If we set _t_ = _ε∥_ _**q** ∥_ 2 _∥_ _**k** ∥_ 2 the above simplifies to:

**==> picture [296 x 28] intentionally omitted <==**

Therefore if _m ≥_[4] 3 _[·]_[1+] _ε_[2] _[ε]_[log][2] _δ_[the][error][bound][follows.][This][completes][the][proof][of][Lemma][3.5][.]

Note that the distortion bound in Lemma 3.5 has remarkably small constants, even smaller than those of the original unquintized JL transform. This indicates that quantizing one of the vectors to just a single sign bit does not result in any loss of accuracy. We use these properties of QJL and our inner product estimator to prove the final approximation bound on our KV cache quantizer.

**Algorithm 1** QJL Key Cache Quantizer

**Input:** Stream of key tokens _**k**_ 1 _,_ _**k**_ 2 _, . . . ∈_ R _[d]_ , integer _m_

- 1: Draw a random sketch _**S** ∈_ R _[m][×][d]_ with i.i.d. entries _**S** i,j ∼N_ (0 _,_ 1) as per Definition 3.1

- 2: **repeat**

- 3: Compute _**k**_[˜] _i ←_ `sign` ( _**Sk** i_ ) and _νi ←∥_ _**k** i∥_ 2

- 4: **store** the quantized vector _k_[˜] _i_ and the key norm _νi_ in the cache

- 5: **until** token stream ends

**Procedure** EstimateScores( _**q** n_ )

**==> picture [407 x 52] intentionally omitted <==**

## **3.1 Key Cache Quantization via QJL**

The key cache is used in the computation of attention scores as shown in Equation (2). To calculate these scores, we need to compute the inner products of the current query embedding with all key embeddings in the cache. We design a quantization scheme that allows for a low-distortion estimate of the inner products between an arbitrary query and all keys in the cache. In this section, we develop a practical algorithm with provable guarantees based on QJL and the inner product estimator defined in Definition 3.1.

The quantization scheme presented in Algorithm 1 applies QJL, defined in Definition 3.1, to each key embedding, mapping them to binary vectors and storing the results in the key cache. We show in the following theorem that the attention scores calculated by Algorithm 1 have very small (1 _± ε_ ) relative distortion with high probability:

**Theorem 3.6** (Distortion bound on QJL key cache quantizer) **.** _For any sequence of key tokens_ _**k**_ 1 _, . . ._ _**k** n ∈_ **R** _[d] and any integer m, Algorithm 1 stores binary vectors_ _**k**_[˜] 1 _, . . ._ _**k**_[˜] _n ∈{−_ 1 _,_ +1 _}[m] along with scalar values ν_ 1 _, . . . νn in the cache. If the key embeddings have bounded norm_ max _i∈_ [ _n_ ] _∥_ _**k** i∥_ 2 _≤ r and m ≥_ 2 _r_[2] _ε[−]_[2] log _n, then for any query embedding_ _**q** n ∈_ **R** _[d] with bounded norm ∥_ _**q** n∥_ 2 _≤ r the output of the procedure EstimateScores(_ _**q** n) satisfies the following with probability_ 1 _−_ `poly` 1( _n_ ) _sinultaneously for all i ∈_ [ _n_ ] _:_

**==> picture [180 x 22] intentionally omitted <==**

_where_ `Score` _is the vector of attention scores defined in Equation_ (2) _._

_Proof._ � The proof is by invoking Lemma 3.5 and a union bound. For every _j ∈_ [ _n_ ] the estimator **qK** ( _j_ ) computed in line 6 of Algorithm 1 is in fact equal to the inner product estimator **qK**[�] ( _j_ ) = `ProdQJL` ( _**q** n,_ _**k** j_ ) as defined in Equation (4). Thus by Lemma 3.5 we have the following with probability at least 1 _− n_[3] _[/]_[(2+2] 1 _[ε]_[)][:]

**==> picture [198 x 21] intentionally omitted <==**

where the second inequality follows from the preconditions of the theorem regarding the boundedness of the norms of the query and key embeddings. By union bound, the above inequality holds simultaneously for all _j ∈_ [ _n_ ] with high probability in _n_ . Thus after applying the softmax function in line 7 of Algorithm 1 we get that with high probability in _n_ :

**==> picture [228 x 15] intentionally omitted <==**

This completes the proof of Theorem 3.6.

This theorem shows that if the query and key embeddings have constant norms, as is common in practical scenarios, we can quantize each key embedding such that only _m ≈ ε[−]_[2] log _n_ bits are needed to store each key token. This is independent of the embedding dimension of the tokens and scales only logarithmically with the sequence length.

## **3.2 Value Cache Quantization**

We quantize the value cache using a standard quantization method, i.e., normalizing each token’s entries and then rounding each entry to a few-bit integer representation. This approach aligns with prior work, which has shown that standard token-wise quantization is highly effective for the value cache and results in a minimal accuracy drop [22, 13].

## **4 Experiments**

In this section, we validate the empirical performance of our algorithm. All experiments are conducted under a single A100 GPU with 80GB memory. We implement two main CUDA kernels for our core primitives: one for quantizing embedding vectors using various floating point data types such as bfloat16, FP16, and FP32, and the other for computing the inner product of an arbitrary embedding vector with all quantized vectors in the cache. The algorithm’s wrapper is implemented in PyTorch, handling all the housekeeping tasks. We plan to complete implementation in the CUDA for future work, which will further accelerate our algorithm.

## **4.1 Practical Consideration**

**Outliers.** As reported in recent works e.g., KIVI [22], KVQuant [13], key embeddings typically contain outliers exhibiting a distinct pattern. Specifically, certain coordinates of key embeddings display relatively large magnitudes. To further investigate these observations, we analyze the distribution of the magnitudes of key embedding coordinates across different layers. Firstly, we observe that there are no significant outliers in the initial attention layers. However, in the deeper layers, certain fixed coordinates of key embeddings consistently exhibit large magnitudes, and this pattern persists within these channels across all tokens. The distribution of outliers across different layers for the Llama-2 model is plotted in Figure 2. It is evident that in the initial layers, outliers are rare, but as we approach the final layers, their frequency and impact increase significantly. Secondly, the outliers show a persistent pattern in specific fixed coordinates of the key embeddings. This observation aligns with previous findings that certain fixed embedding coordinates exhibit larger outliers [9, 20, 22, 13].

As demonstrated in Theorem 3.6, the distortion on the attention scores is directly proportional to the norms of the embeddings. Therefore, capturing these outlier coordinates is essential, as their large magnitudes contribute significantly to the norms of key embeddings. By identifying and isolating these outlier channels, we can reduce the norm of the key embeddings and, consequently, significantly decrease the final distortion. Next, we quantize the outliers using an independent instance of our QJL quantizer but with a lower compression rate, utilizing more bits to accurately represent each outlier coordinate.

**Orthogonalized JL transform.** We observed that orthogonalizing the rows of the JL matrix _S_ in Definition 3.1 almost always improves the performance of our QJL quantizer. This finding aligns

**==> picture [468 x 142] intentionally omitted <==**

**----- Start of picture text -----**<br>
14 7 14 8<br>1.52.02.5 1.00.8 106128 654 106128 765<br>0.51.0 0.6 24 3 24 43<br>0.0 0.4 0 2 0 2<br>1400 0.2 1400 1 1400 1<br>1200 1200 1200<br>1000 1000 1000<br>0 20 40 60 80 100 120 0 200400600800 0 20 40 60 80 100 120 0 200400600800 0 20 40 60 80 100 120 0 200400600800<br>(a) Layer 0, Head 0 (b) Layer 15, Head 0 (c) Layer 31, Head 0<br>Channels (Sorted) Channels (Sorted) Channels (Sorted)<br>Tokens Tokens Tokens<br>Magnitude Magnitude Magnitude<br>**----- End of picture text -----**<br>

Figure 2: The magnitude of key cache entries for different layers of the Llama-2 model, based on an example prompt, reveals notable patterns. The coordinates of embeddings (channels) are sorted by their average magnitude over tokens. In the initial layers, no significant outlier patterns are observed. However, in the deeper layers, a few channels (approximately four) exhibit visibly larger magnitudes, indicating the presence of significant outliers. This observation highlights the importance of addressing these outliers to improve quantization accuracy and reduce distortion in the key cache.

with previous work on various applications of the JL transform, such as random Fourier features [35] and locality sensitive hashing [14]. Consequently, in our implementation and all experiments, we first generate a random JL matrix _S_ with i.i.d. Gaussian entries and then orthogonalize its rows using QR decomposition. We then use this orthogonalized matrix in our QJL quantizer, as described in Algorithm 1.

## **4.2 End-to-end text generation**

Next we benchmark our method on LongBench [4], a benchmark of long-range context on various tasks. We choose the base model as longchat-7b-v1.5-32k [19] (fine-tuned Llama-2 with 7B parameter with 16,384 context length) and apply following quantization methods to this model; KIVI [22], KVQuant [36] and our proposed quantization via QJL. Each floating-point number (FPN) in the base model is represented by 16 bits, and we choose proper hyper-parameters of KIVI and QJL so that their bits per FPN become 3. For KVQuant, we follow the default setting which holds its bits per FPN as 4.3. To validate the quality of those quantized models, we benchmark them on 6 question-answer datasets from LongBench [4], and we set the maximum sequence length to 31,500. We follow the same approach of prompting and evaluating to evaluate the prediction of the model from the original repository. Table 1 summarizes the results. Our proposed QJL achieves the highest F1 score within the quantization methods for `NarrativeQA, Qasper` and `2WikiMultiQA` . Although KVQuant performs better than other methods for `MultiQA-en` dataset, it requires a huge amount of preprocessing which leads to slow runtime. To validate this, we additionally report runtime of prompt encoding, KV cache quantization, and decoding (token generation) in a single attention layer. Figure 3 shows the wall-clock time to encode a prompt and quantize the KV cache, generate 128 tokens for llama2 model, and generate 64 tokens for llama3 model using different quantization methods in a single attention layer of these models. Note that QJL is the only method that can quantize Llama3, as our kernels support grouped query attention and BF16 data type. we observe the same speed for Llama3 as the exact method for generation. The input sequence lengths vary between 1k to 128k. As shown in Figure 3, KVQuant runs slower than other methods during both prompt encoding and decoding phases. On the other hand, both KIVI and our QJL with 3

| Methods<br>Bits                                                                   | Datasets from LongBench [4]                                                                                                                                                                                                                  |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|                                                                                   | `NarrativeQA`<br>`Qasper`<br>`MultiQA-en`<br>`MultifQA-zh`<br>`HotpotQA`<br>`2WikiMultiQA`                                                                                                                                                   |
| FP16 (baseline)<br>16<br>KIVI [22]<br>3<br>KVQuant [13]<br>4.3<br>QJL (ours)<br>3 | 20.79<br>29.42<br>42.83<br>34.33<br>33.05<br>24.14<br>20.96<br>29.01<br>40.93<br>**34.75**<br>32.79<br>23.01<br>20.14<br>28.77<br>**44.22**<br>34.44<br>34.06<br>23.05<br>**21.83**<br>**29.44**<br>41.52<br>34.42<br>**35.62**<br>**23.60** |

Table 1: Evaluation (F1 scores) of various quantization methods on long-context question-answering datasets from LongBench [4]. We set bits per floating-point number (FPN) to 3. Bold indicates the highest scores within quantization methods.

| Models<br>Methods<br>Bits                                                | Datasets from LM-eval [12]                                                                                                          |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
|                                                                          | `Lambada-OpenAI`<br>`HellaSwag`<br>`PIQA`<br>`MathQA`<br>`MMLU`                                                                     |
| Llama-2-7B<br>FP16 (baseline)<br>16<br>KIVI [22]<br>3<br>QJL (ours)<br>3 | 73.90<br>57.18<br>78.07<br>28.11<br>41.85<br>73.88<br>57.13<br>78.07<br>28.11<br>41.81<br>73.88<br>57.14<br>78.07<br>28.17<br>41.78 |
| Llama-3-8B<br>BF16 (baseline)<br>16<br>QJL (ours)<br>3                   | 75.59<br>60.17<br>79.65<br>40.64<br>62.09<br>75.61<br>60.13<br>79.87<br>40.60<br>62.12                                              |

Table 2: Evaluation (accuracy) of various quantization methods on regular length datasets from LM-eval [12]. These comparisons are not typically based on long-context length; however, as evident, even in these cases, our QJL with 3 bits per FPN performs comparably to the baseline with 16 bits per FPN.

bits per FPN show marginal runtime overhead compared to the exact baseline during prompting but reduce KV cache memory usage by at least a factor of 5.

We additionally test our method on datasets `Lambada-OpenAI` , `HellaSwag` , `PIQA` , `MathQA` , and `MMLU` , which have shorter sequence lengths. We benchmark our method using LM-eval [12] framework to ensure a thorough evaluation across various metrics. We evaluate quantization methods with accuracy across Llama-2-7B [31] and Llama-3-8B [23] models. Note that KIVI only supports a half-precision floating point, whereas our method can be used for any precision format type. This makes it unable to run KIVI on the Llama-3 model.

As a results, QJL can significantly reduce memory usage by utilizing only 3 bits per FPN, compared to the 16 bits per FPN in the baseline, achieving around an 81% reduction in memory. We observe that this efficiency does not compromise performance significantly. Across all datasets, our method’s accuracy is generally comparable to the baseline, with slight variations. In Table 2, our QJL on the Llama-3-8B performs on average about slightly better than the baseline across all datasets.

## **References**

- [1] Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat, et al. Gpt-4 technical report. _arXiv preprint arXiv:2303.08774_ , 2023.

**==> picture [469 x 153] intentionally omitted <==**

**----- Start of picture text -----**<br>
6<br>1 . 5 FP16 1 . 5<br>FP16<br>QJL (ours)<br>QJL (ours) 4 KVQuant<br>1 . 0 KVQuant KIVI 1 . 0<br>KIVI<br>BF16<br>0 . 5 2 0 . 5 QJL (ours)<br>0 . 0 0 0 . 0<br>2k 8k 32k 64k 2k 8k 32k 64k 1k 2k 8k 32k 64k<br>token length token length token length<br>(a) Prompt encoding (Llama2) (b) Token generation (Llama2) (c) Encode and generate (Llama3)<br>total (ms)<br>decode (ms)<br>encode + quantize (ms)<br>**----- End of picture text -----**<br>

Figure 3: Wall-clock time (ms) to encode a prompt and quantize the KV cache (left), generate 128 tokens for llama2 model (middle), and generate 64 tokens for llama3 model (right) using different quantization methods in a single attention layer model. The input sequence length varies from 1k to 64k. Both KIVI and QJL (ours) with 3 bits per FPN show faster decoding time than the baseline. However, KVQuant is significantly slower during both quantizing and decoding phases. QJL is the only method that can quantize Llama3, as our kernels support grouped query attention and BF16 data type. We observe the same speed for Llama3 as the exact method for generation. Note that our memory usage is at least 5-fold less than the exact method and can support all data types.

- [2] Joshua Ainslie, James Lee-Thorp, Michiel de Jong, Yury Zemlyanskiy, Federico Lebron, and Sumit Sanghai. Gqa: Training generalized multi-query transformer models from multi-head checkpoints. In _Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing_ , pages 4895–4901, 2023.

- [3] Antropic. claude, 2024. `https://www.anthropic.com/news/claude-3-family` .

- [4] Yushi Bai, Xin Lv, Jiajie Zhang, Hongchang Lyu, Jiankai Tang, Zhidian Huang, Zhengxiao Du, Xiao Liu, Aohan Zeng, Lei Hou, Yuxiao Dong, Jie Tang, and Juanzi Li. Longbench: A bilingual, multitask benchmark for long context understanding. _arXiv preprint arXiv:2308.14508_ , 2023.

- [5] Stéphane Boucheron, Gábor Lugosi, and Olivier Bousquet. Concentration inequalities. In _Summer school on machine learning_ , pages 208–240. Springer, 2003.

- [6] Moses S Charikar. Similarity estimation techniques from rounding algorithms. In _Proceedings of the thiry-fourth annual ACM symposium on Theory of computing_ , pages 380–388, 2002.

- [7] Microsoft Copilot, 2023. `https://github.com/features/copilot` .

- [8] Sanjoy Dasgupta and Anupam Gupta. An elementary proof of a theorem of johnson and lindenstrauss. _Random Structures & Algorithms_ , 22(1):60–65, 2003.

- [9] Tim Dettmers, Mike Lewis, Younes Belkada, and Luke Zettlemoyer. Gpt3. int8 (): 8-bit matrix multiplication for transformers at scale. _Advances in Neural Information Processing Systems_ , 35:30318–30332, 2022.

- [10] Shichen Dong, Wen Cheng, Jiayu Qin, and Wei Wang. Qaq: Quality adaptive quantization for llm kv cache. _arXiv preprint arXiv:2403.04643_ , 2024.

- [11] Adobe FireFly, 2023. `https://firefly.adobe.com/` .

- [12] Leo Gao, Jonathan Tow, Baber Abbasi, Stella Biderman, Sid Black, Anthony DiPofi, Charles Foster, Laurence Golding, Jeffrey Hsu, Alain Le Noac’h, Haonan Li, Kyle McDonell, Niklas Muennighoff, Chris Ociepa, Jason Phang, Laria Reynolds, Hailey Schoelkopf, Aviya Skowron, Lintang Sutawika, Eric Tang, Anish Thite, Ben Wang, Kevin Wang, and Andy Zou. A framework for few-shot language model evaluation, 2023. `https://github.com/EleutherAI/ lm-evaluation-harness` .

- [13] Coleman Hooper, Sehoon Kim, Hiva Mohammadzadeh, Michael W Mahoney, Yakun Sophia Shao, Kurt Keutzer, and Amir Gholami. KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization. _arXiv preprint arXiv:2401.18079_ , 2024.

- [14] Jianqiu Ji, Jianmin Li, Shuicheng Yan, Bo Zhang, and Qi Tian. Super-bit locality-sensitive hashing. _Advances in neural information processing systems_ , 25, 2012.

- [15] William B Johnson, Joram Lindenstrauss, and Gideon Schechtman. Extensions of Lipschitz maps into Banach spaces. _Israel Journal of Mathematics_ .

- [16] Hao Kang, Qingru Zhang, Souvik Kundu, Geonhwa Jeong, Zaoxing Liu, Tushar Krishna, and Tuo Zhao. Gear: An efficient kv cache compression recipefor near-lossless generative inference of llm. _arXiv preprint arXiv:2403.05527_ , 2024.

- [17] Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei. Scaling laws for neural language models. _arXiv preprint arXiv:2001.08361_ , 2020.

- [18] Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying Sheng, Lianmin Zheng, Cody Hao Yu, Joseph Gonzalez, Hao Zhang, and Ion Stoica. Efficient memory management for large language model serving with pagedattention. In _Proceedings of the 29th Symposium on Operating Systems Principles_ , pages 611–626, 2023.

- [19] Dacheng Li, Rulin Shao, Anze Xie, Ying Sheng, Lianmin Zheng, Joseph Gonzalez, Ion Stoica, Xuezhe Ma, and Hao Zhang. How long can open-source llms truly promise on context length?, 2023. `https://huggingface.co/lmsys/longchat-7b-v1.5-32k` .

- [20] Ji Lin, Jiaming Tang, Haotian Tang, Shang Yang, Xingyu Dang, and Song Han. Awq: Activationaware weight quantization for llm compression and acceleration. _arXiv preprint arXiv:2306.00978_ , 2023.

- [21] Zichang Liu, Aditya Desai, Fangshuo Liao, Weitao Wang, Victor Xie, Zhaozhuo Xu, Anastasios Kyrillidis, and Anshumali Shrivastava. Scissorhands: Exploiting the persistence of importance hypothesis for llm kv cache compression at test time. _Advances in Neural Information Processing Systems_ , 36, 2024.

- [22] Zirui Liu, Jiayi Yuan, Hongye Jin, Shaochen Zhong, Zhaozhuo Xu, Vladimir Braverman, Beidi Chen, and Xia Hu. Kivi: A tuning-free asymmetric 2bit quantization for kv cache. _arXiv preprint arXiv:2402.02750_ , 2024.

- [23] Llama3, 2024. `https://github.com/meta-llama/llama3` .

- [24] Midjourney, 2022. `https://www.midjourney.com/home` .

- [25] OpenAI. Introducing gpt-4o, 2024. `https://openai.com/index/hello-gpt-4o/` .

- [26] OpenAI. Sora: Creating video from text, 2024. `https://openai.com/index/sora/` .

- [27] Reiner Pope, Sholto Douglas, Aakanksha Chowdhery, Jacob Devlin, James Bradbury, Jonathan Heek, Kefan Xiao, Shivani Agrawal, and Jeff Dean. Efficiently scaling transformer inference. _Proceedings of Machine Learning and Systems_ , 5, 2023.

- [28] Aditya Ramesh, Prafulla Dhariwal, Alex Nichol, Casey Chu, and Mark Chen. Hierarchical text-conditional image generation with clip latents. _arXiv preprint arXiv:2204.06125_ , 2022.

- [29] Noam Shazeer. Fast transformer decoding: One write-head is all you need. _arXiv preprint arXiv:1911.02150_ , 2019.

- [30] Ying Sheng, Lianmin Zheng, Binhang Yuan, Zhuohan Li, Max Ryabinin, Beidi Chen, Percy Liang, Christopher Ré, Ion Stoica, and Ce Zhang. Flexgen: High-throughput generative inference of large language models with a single gpu. In _International Conference on Machine Learning_ , pages 31094–31116. PMLR, 2023.

- [31] Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale, et al. Llama 2: Open foundation and fine-tuned chat models. _arXiv preprint arXiv:2307.09288_ , 2023.

- [32] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Lukasz Kaiser, and Illia Polosukhin. Attention is all you need. 2017.

- [33] Guangxuan Xiao, Yuandong Tian, Beidi Chen, Song Han, and Mike Lewis. Efficient streaming language models with attention sinks. _arXiv preprint arXiv:2309.17453_ , 2023.

- [34] June Yong Yang, Byeongwook Kim, Jeongin Bae, Beomseok Kwon, Gunho Park, Eunho Yang, Se Jung Kwon, and Dongsoo Lee. No token left behind: Reliable kv cache compression via importance-aware mixed precision quantization. _arXiv preprint arXiv:2402.18096_ , 2024.

- [35] Felix Xinnan X Yu, Ananda Theertha Suresh, Krzysztof M Choromanski, Daniel N HoltmannRice, and Sanjiv Kumar. Orthogonal random features. _Advances in neural information processing systems_ , 29, 2016.

- [36] Yuxuan Yue, Zhihang Yuan, Haojie Duanmu, Sifan Zhou, Jianlong Wu, and Liqiang Nie. Wkvquant: Quantizing weight and key/value cache for large language models gains more. _arXiv preprint arXiv:2402.12065_ , 2024.

- [37] Amir Zandieh, Insu Han, Vahab Mirrokni, and Amin Karbasi. Subgen: Token generation in sublinear time and memory. _arXiv preprint arXiv:2402.06082_ , 2024.

- [38] Tianyi Zhang, Jonah Yi, Zhaozhuo Xu, and Anshumali Shrivastava. Kv cache is 1 bit per channel: Efficient large language model inference with coupled quantization. _arXiv preprint arXiv:2405.03917_ , 2024.

- [39] Zhenyu Zhang, Ying Sheng, Tianyi Zhou, Tianlong Chen, Lianmin Zheng, Ruisi Cai, Zhao Song, Yuandong Tian, Christopher Ré, Clark Barrett, et al. H2o: Heavy-hitter oracle for efficient generative inference of large language models. _Advances in Neural Information Processing Systems_ , 36, 2024.
